import streamlit as st
import pandas as pd
# import xlsxwriter
import warnings

warnings.filterwarnings('ignore')
def add_row_to_dataframe(df, new_row):
    if df is None:
        # Create a new DataFrame if it doesn't exist
        df = new_row
    else:
        # Append the new row to the existing DataFrame
        df = pd.concat([df, new_row], ignore_index=True)
    return df
def index_to_excel_col(index):
    col_str = ''
    while index >= 0:
        col_str = chr(index % 26 + 67) + col_str
        index = index // 26 - 1
    return col_str

st.header("Sheet view")
xlfile1 = st.sidebar.file_uploader("Upload Excel file", type=['xlsx'],key='file1')
xlfile2 = st.sidebar.file_uploader("Upload Excel file", type=['xlsx'],key='file2')

if xlfile1 and xlfile2:
    xls = pd.ExcelFile(xlfile1)
    sheet_selector = st.sidebar.selectbox("Select sheet:", xls.sheet_names)   
    header = st.sidebar.number_input("Header (row number)", min_value=0, value=0, step=1)
    df1 = pd.read_excel(xlfile1, sheet_name=sheet_selector,header=header)
    df2 = pd.read_excel(xlfile2, sheet_name=sheet_selector,header=header)
    UniqueRow = st.sidebar.selectbox("Primary Key/ Unique Value column", df1.columns) 

    st.markdown(f"### Currently Selected: `{sheet_selector}`")
    df1.index = df1.index + 1
    df2.index = df2.index + 1
    st.write(df1)
    st.write(df2)
    if UniqueRow:
        df1=df1[[UniqueRow]+[c for c in df1 if c !=UniqueRow]]
        df2=df2[[UniqueRow]+[c for c in df2 if c !=UniqueRow]]

        #line below is error handling in case one file is empty, doesnt has unique row, or wrong header is selected
        if UniqueRow not in df1.columns or UniqueRow not in df2.columns:
            print("The unique row",UniqueRow,"could not be found in one of the sheets, please check the headers and if they contain unique row")
            print("current file headers for file 1:",df1.columns,"\ncurrent file headers for file 2:",df2.columns)
            quit()
        uid1list = df1[UniqueRow].tolist()
        uid2list = df2[UniqueRow].tolist()
        set1 = set(uid1list)
        set2 = set(uid2list)

        unique_elements = set1.symmetric_difference(set2)
        unique_from_list1 = unique_elements.intersection(set1)
        unique_from_list2 = unique_elements.intersection(set2)
        onlyonefiledataframe=None
        for uniques1 in unique_from_list1:
            ind1=uid1list.index(uniques1)
            row_df1 = df1.iloc[[ind1]].copy()
            row_df1['source'] = xlfile1.name
            onlyonefiledataframe = add_row_to_dataframe(onlyonefiledataframe, row_df1)
        # empty line
        if onlyonefiledataframe is not None and not onlyonefiledataframe.empty:
            onlyonefiledataframe.loc[len(onlyonefiledataframe)] = [None] * len(onlyonefiledataframe.columns)

        #...........
        for uniques2 in unique_from_list2:
            ind2=uid2list.index(uniques2)
            row_df2 = df2.iloc[[ind2]].copy()
            row_df2['source'] = xlfile2.name
            onlyonefiledataframe = add_row_to_dataframe(onlyonefiledataframe, row_df2)
        if onlyonefiledataframe is not None:
            onlyonefiledataframe = onlyonefiledataframe[[UniqueRow, 'source'] + [c for c in df2.columns if c not in [UniqueRow, 'source']]]
        else:
            raise ValueError("onlyonefiledataframe is None after processing")


        #the next program creates second sheet for checking values which are different, but having same unique identifier
        df = None
        for uid in uid1list:
            if uid in uid2list:
                ind1=uid1list.index(uid)
                ind2=uid2list.index(uid)
                row_df1 = df1.iloc[[ind1]].copy()
                row_df2 = df2.iloc[[ind2]].copy()
                # are_not_equal = not row_df1.equals(row_df2)
                # if are_not_equal==True:
                differing_columns = []
                # print(row_df1)
                for col in row_df1.columns:
                    val1 = row_df1[col].values[0]
                    val2 = row_df2[col].values[0]
                    if pd.isna(val1) and pd.isna(val2):
                        continue  # Both are NaN, so they are considered equal
                    if val1 != val2:
                        excel_col = index_to_excel_col(row_df1.columns.get_loc(col))
                        differing_columns.append(f"{col}({excel_col})")
                if len(differing_columns)>0:
                    comments = ', '.join(differing_columns)
                    row_df1.insert(1, 'Comments', f"{len(differing_columns)} mismatched")
                    row_df1.insert(2, 'Unmatched Column', comments)
                    row_df2['Unmatched Column(column id)'] = comments
                    row_df1['--------------------'] = "----------------"
                    row_df1['------------------'] = "--------------------"
                    rowdf = pd.concat([row_df1, row_df2], axis=1)
                    df = add_row_to_dataframe(df, rowdf)

            #error handling otherwise if same files are compared these dataframes are never made and object type stays None empty causing 
            # error 'NoneType' object has no attribute 'to_excel'
        
        with pd.ExcelWriter('combined.xlsx') as writer:
            onlyonefiledataframe.to_excel(writer, sheet_name='Missing', index=False)
            df.to_excel(writer, sheet_name='MisMatched', index=False)
            
        
        # Download button for the combined Excel file
        with open('combined.xlsx', 'rb') as f:
            st.sidebar.download_button(
                label="Download Excel file",
                data=f,
                file_name='combined.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        

