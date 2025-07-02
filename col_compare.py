import streamlit as st
import pandas as pd
import io

st.title("🔍 Excel Comparator (Full Rows from Multi-Column Match)")

file1 = st.file_uploader("📄 Upload First Excel File", type=["xlsx", "xls"], key="file1")
file2 = st.file_uploader("📄 Upload Second Excel File", type=["xlsx", "xls"], key="file2")

if file1 and file2:
    xls1 = pd.ExcelFile(file1)
    xls2 = pd.ExcelFile(file2)

    sheet1 = st.selectbox("📑 Select sheet from File 1", xls1.sheet_names, key="sheet1")
    sheet2 = st.selectbox("📑 Select sheet from File 2", xls2.sheet_names, key="sheet2")

    df1 = pd.read_excel(xls1, sheet_name=sheet1)
    df2 = pd.read_excel(xls2, sheet_name=sheet2)

    st.write("**File 1 Preview:**")
    st.dataframe(df1.head())

    st.write("**File 2 Preview:**")
    st.dataframe(df2.head())

    st.subheader("🔧 Select columns to match by")
    cols1 = st.multiselect("File 1 columns", df1.columns, key="cols1")
    cols2 = st.multiselect("File 2 columns", df2.columns, key="cols2")

    if len(cols1) != len(cols2):
        st.warning("⚠️ Please select the same number of columns from both files.")
    elif cols1 and cols2 and st.button("🔍 Compare Now"):
        # Create composite key in both dataframes
        df1["__key__"] = df1[cols1].astype(str).agg(" | ".join, axis=1)
        df2["__key__"] = df2[cols2].astype(str).agg(" | ".join, axis=1)

        # Identify match and mismatch sets
        keys1 = set(df1["__key__"].dropna())
        keys2 = set(df2["__key__"].dropna())

        match_keys = keys1 & keys2
        only1_keys = keys1 - keys2
        only2_keys = keys2 - keys1

        # Filter full rows
        df_match1 = df1[df1["__key__"].isin(match_keys)].drop(columns="__key__")
        df_only1 = df1[df1["__key__"].isin(only1_keys)].drop(columns="__key__")
        df_match2 = df2[df2["__key__"].isin(match_keys)].drop(columns="__key__")
        df_only2 = df2[df2["__key__"].isin(only2_keys)].drop(columns="__key__")

        st.success(f"✅ Matches: {len(df_match1)} rows")
        st.info(f"📁 Only in File 1: {len(df_only1)} rows")
        st.info(f"📁 Only in File 2: {len(df_only2)} rows")

        # Show expandable results
        with st.expander("🎯 Matched Rows from File 1"):
            st.dataframe(df_match1)
        with st.expander("🎯 Matched Rows from File 2"):
            st.dataframe(df_match2)
        with st.expander("❌ Only in File 1"):
            st.dataframe(df_only1)
        with st.expander("❌ Only in File 2"):
            st.dataframe(df_only2)

        # Export as Excel
        def create_excel_file():
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_match1.to_excel(writer, sheet_name="Matched_File1", index=False)
                df_match2.to_excel(writer, sheet_name="Matched_File2", index=False)
                df_only1.to_excel(writer, sheet_name="Only_in_File1", index=False)
                df_only2.to_excel(writer, sheet_name="Only_in_File2", index=False)
            output.seek(0)
            return output

        excel_output = create_excel_file()

        st.download_button("⬇️ Download Results as Excel", excel_output,
                           file_name="comparison_full_rows.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # Optional CSVs
        st.download_button("⬇️ CSV: Only in File 1", df_only1.to_csv(index=False), "only_in_file1.csv", "text/csv")
        st.download_button("⬇️ CSV: Only in File 2", df_only2.to_csv(index=False), "only_in_file2.csv", "text/csv")
        st.download_button("⬇️ CSV: Matched Rows File 1", df_match1.to_csv(index=False), "matched_file1.csv", "text/csv")
        st.download_button("⬇️ CSV: Matched Rows File 2", df_match2.to_csv(index=False), "matched_file2.csv", "text/csv")
