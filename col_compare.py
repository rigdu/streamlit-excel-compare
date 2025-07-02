import streamlit as st
import pandas as pd
import io

st.title("🔍 Excel Comparator — Side-by-Side Merged View")

file1 = st.file_uploader("📄 Upload First Excel File", type=["xlsx", "xls"], key="file1")
file2 = st.file_uploader("📄 Upload Second Excel File", type=["xlsx", "xls"], key="file2")

if file1 and file2:
    xls1 = pd.ExcelFile(file1)
    xls2 = pd.ExcelFile(file2)

    sheet1 = st.selectbox("📑 Select sheet from File 1", xls1.sheet_names, key="sheet1")
    sheet2 = st.selectbox("📑 Select sheet from File 2", xls2.sheet_names, key="sheet2")

    df1 = pd.read_excel(xls1, sheet_name=sheet1)
    df2 = pd.read_excel(xls2, sheet_name=sheet2)

    st.write("**Preview - File 1**")
    st.dataframe(df1.head())

    st.write("**Preview - File 2**")
    st.dataframe(df2.head())

    st.subheader("🔧 Select columns to use as unique key")
    cols1 = st.multiselect("File 1 key columns", df1.columns, key="cols1")
    cols2 = st.multiselect("File 2 key columns", df2.columns, key="cols2")

    if len(cols1) != len(cols2):
        st.warning("⚠️ Select same number of columns in both files")
    elif cols1 and cols2 and st.button("🔍 Compare Now"):
        # Step 1: Create matching keys
        df1["__key__"] = df1[cols1].astype(str).agg(" | ".join, axis=1)
        df2["__key__"] = df2[cols2].astype(str).agg(" | ".join, axis=1)

        # Match keys
        match_keys = set(df1["__key__"]).intersection(set(df2["__key__"]))
        only1_keys = set(df1["__key__"]) - set(df2["__key__"])
        only2_keys = set(df2["__key__"]) - set(df1["__key__"])

        df_match1 = df1[df1["__key__"].isin(match_keys)].copy()
        df_match2 = df2[df2["__key__"].isin(match_keys)].copy()
        df_only1 = df1[df1["__key__"].isin(only1_keys)].drop(columns="__key__")
        df_only2 = df2[df2["__key__"].isin(only2_keys)].drop(columns="__key__")

        df_match1.set_index("__key__", inplace=True)
        df_match2.set_index("__key__", inplace=True)

        # Step 2: Merge on __key__
        merged = pd.merge(df_match1.add_prefix("F1_"),
                          df_match2.add_prefix("F2_"),
                          left_index=True, right_index=True,
                          how="inner").reset_index().rename(columns={"__key__": "Match_Key"})

        st.success(f"✅ Matches: {len(merged)}")
        st.info(f"📁 Only in File 1: {len(df_only1)}")
        st.info(f"📁 Only in File 2: {len(df_only2)}")

        # Step 3: Show merged view
        with st.expander("🎯 Merged View of Matched Rows (Side-by-Side)"):
            st.dataframe(merged)

        with st.expander("❌ Only in File 1"):
            st.dataframe(df_only1)

        with st.expander("❌ Only in File 2"):
            st.dataframe(df_only2)

        # Step 4: Optional highlighting (Differences)
        def highlight_diff(row):
            styles = []
            for col in row.index:
                if col.startswith("F1_"):
                    col_f2 = col.replace("F1_", "F2_")
                    if col_f2 in row.index:
                        styles.append("background-color: red" if row[col] != row[col_f2] else "")
                    else:
                        styles.append("")
                else:
                    styles.append("")
            return styles

        st.subheader("🎨 Highlighted Differences")
        st.dataframe(merged.style.apply(highlight_diff, axis=1))

        # Step 5: Download
        def create_excel():
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                merged.to_excel(writer, sheet_name="Matched_SideBySide", index=False)
                df_only1.to_excel(writer, sheet_name="Only_in_File1", index=False)
                df_only2.to_excel(writer, sheet_name="Only_in_File2", index=False)
            buffer.seek(0)
            return buffer

        excel_output = create_excel()

        st.download_button("⬇️ Download All Results as Excel", excel_output,
                           file_name="comparison_merged.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
