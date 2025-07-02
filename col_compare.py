import streamlit as st
import pandas as pd
import io

st.title("🔍 Excel File Comparator (Multi-Column Support)")

# Step 1: Upload files
file1 = st.file_uploader("📄 Upload First Excel File", type=["xlsx", "xls"], key="file1")
file2 = st.file_uploader("📄 Upload Second Excel File", type=["xlsx", "xls"], key="file2")

if file1 and file2:
    # Load Excel files
    xls1 = pd.ExcelFile(file1)
    xls2 = pd.ExcelFile(file2)

    sheet1 = st.selectbox("📑 Select sheet from File 1", xls1.sheet_names, key="sheet1")
    sheet2 = st.selectbox("📑 Select sheet from File 2", xls2.sheet_names, key="sheet2")

    df1 = pd.read_excel(xls1, sheet_name=sheet1)
    df2 = pd.read_excel(xls2, sheet_name=sheet2)

    st.subheader("📋 File Previews")
    st.write("**File 1 Preview:**")
    st.dataframe(df1.head())

    st.write("**File 2 Preview:**")
    st.dataframe(df2.head())

    # Multi-column selection
    st.subheader("🔧 Select columns to compare (combined key)")
    cols1 = st.multiselect("Select columns from File 1", df1.columns, key="cols1")
    cols2 = st.multiselect("Select columns from File 2", df2.columns, key="cols2")

    # Check if same number of columns are selected
    if len(cols1) != len(cols2):
        st.warning("⚠️ Please select the same number of columns in both files.")
    elif cols1 and cols2 and st.button("🔍 Compare Now"):
        # Create keys by concatenating column values
        df1["__compare_key__"] = df1[cols1].astype(str).agg(" | ".join, axis=1)
        df2["__compare_key__"] = df2[cols2].astype(str).agg(" | ".join, axis=1)

        set1 = set(df1["__compare_key__"].dropna())
        set2 = set(df2["__compare_key__"].dropna())

        matches = sorted(set1 & set2)
        only_in_file1 = sorted(set1 - set2)
        only_in_file2 = sorted(set2 - set1)

        df_match = pd.DataFrame(matches, columns=["Matched Key"])
        df_only1 = pd.DataFrame(only_in_file1, columns=["Only in File 1"])
        df_only2 = pd.DataFrame(only_in_file2, columns=["Only in File 2"])

        st.success(f"✅ {len(matches)} matches found.")
        st.info(f"📁 {len(only_in_file1)} unique in File 1.")
        st.info(f"📁 {len(only_in_file2)} unique in File 2.")

        with st.expander("🎯 Matches"):
            st.dataframe(df_match)

        with st.expander("❌ Only in File 1"):
            st.dataframe(df_only1)

        with st.expander("❌ Only in File 2"):
            st.dataframe(df_only2)

        # Excel Download Function
        def to_excel_download(dfs: dict):
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                for name, df in dfs.items():
                    df.to_excel(writer, sheet_name=name, index=False)
            buffer.seek(0)
            return buffer

        excel_file = to_excel_download({
            "Matches": df_match,
            "Only_in_File1": df_only1,
            "Only_in_File2": df_only2
        })

        # Download Buttons
        st.download_button("⬇️ Download All Results (Excel)", excel_file,
                           file_name="comparison_results.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        st.download_button("⬇️ Download Matches (CSV)", df_match.to_csv(index=False), "matches.csv", "text/csv")
        st.download_button("⬇️ Download Only in File 1 (CSV)", df_only1.to_csv(index=False), "only_in_file1.csv", "text/csv")
        st.download_button("⬇️ Download Only in File 2 (CSV)", df_only2.to_csv(index=False), "only_in_file2.csv", "text/csv")
