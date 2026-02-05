import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CẤU HÌNH HỆ THỐNG & CSS TÙY CHỈNH ---
pd.set_option("styler.render.max_elements", 2000000)

st.set_page_config(
    page_title="Health Analytics Pro",
    page_icon="",
    layout="wide"
)

# CSS để fix lỗi Ctrl + P và làm đẹp giao diện
st.markdown("""
    <style>
    /* Làm đẹp thẻ Metric */
    [data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* FIX LỖI IN ẤN (CTRL + P) */
    @media print {
        [data-testid="stSidebar"], header, footer, .stDeployButton {
            display: none !important;
        }
        .main .block-container {
            max-width: 100% !important;
            padding: 0 !important;
        }
        .stPlotlyChart {
            page-break-inside: avoid !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM MAPPING DỮ LIỆU (SCALE) ---
def get_mappings():
    return {
        'Diabetes_Label': {0: 'Khỏe mạnh', 1: 'Tiền tiểu đường', 2: 'Tiểu đường'},
        'GenHlth_Label': {1: 'Rất tốt', 2: 'Tốt', 3: 'Khá', 4: 'Tạm ổn', 5: 'Yếu'},
        'Age_Label': {
            1: '18-24', 2: '25-29', 3: '30-34', 4: '35-39', 5: '40-44', 
            6: '45-49', 7: '50-54', 8: '55-59', 9: '60-64', 10: '65-69', 
            11: '70-74', 12: '75-79', 13: '80+'
        },
        'Education_Label': {
            1: 'Mầm non/Chưa đi học', 2: 'Cấp 1-2', 3: 'Cấp 3 (Chưa tốt nghiệp)', 
            4: 'Tốt nghiệp Cấp 3', 5: 'Cao đẳng', 6: 'Đại học trở lên'
        },
        'Income_Label': {
            1: '<$10k', 2: '$10k-15k', 3: '$15k-20k', 4: '$20k-25k', 
            5: '$25k-35k', 6: '$35k-50k', 7: '$50k-75k', 8: '>$75k'
        }
    }

@st.cache_data
def load_and_scale_data():
    try:
        df = pd.read_csv('data.csv')
        maps = get_mappings()
        
        # Áp dụng mapping (tạo cột mới để không làm mất dữ liệu gốc)
        # Kiểm tra nếu cột tồn tại thì mới map
        if 'Diabetes_012' in df.columns:
            df['Diabetes_Status'] = df['Diabetes_012'].map(maps['Diabetes_Label'])
        elif 'Diabetes_binary' in df.columns:
            df['Diabetes_Status'] = df['Diabetes_binary'].map({0: 'Khỏe mạnh', 1: 'Tiểu đường'})
            
        df['Age_Range'] = df['Age'].map(maps['Age_Label'])
        df['General_Health'] = df['GenHlth'].map(maps['GenHlth_Label'])
        
        return df
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return None

# --- 3. GIAO DIỆN ---
def main():
    df = load_and_scale_data()
    if df is None: return

    maps = get_mappings()

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("Bộ lọc chuyên sâu")
        
        # Lọc theo nhóm tuổi (Dùng nhãn đã map)
        selected_ages = st.multiselect(
            "Chọn nhóm tuổi", 
            options=list(maps['Age_Label'].values()),
            default=list(maps['Age_Label'].values())[6:10] # Mặc định chọn trung niên
        )
        
        # Lọc theo giới tính
        gender = st.radio("Giới tính", options=["Tất cả", "Nam", "Nữ"], horizontal=True)
        
        st.divider()
        #st.write("Nhấn Ctrl + P để xuất báo cáo PDF*")

    # --- XỬ LÝ DỮ LIỆU ---
    filtered_df = df[df['Age_Range'].isin(selected_ages)]
    if gender == "Nam":
        filtered_df = filtered_df[filtered_df['Sex'] == 1]
    elif gender == "Nữ":
        filtered_df = filtered_df[filtered_df['Sex'] == 0]

    # --- TIÊU ĐỀ ---
    st.title("Hệ thống Phân tích Chỉ số Sức khỏe")
    st.caption("Dữ liệu được chuẩn hóa theo tiêu chuẩn CDC BRFSS")

    # --- METRICS ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng số mẫu", f"{len(filtered_df):,}")
    c2.metric("BMI Trung bình", f"{filtered_df['BMI'].mean():.1f}")
    c3.metric("Tỷ lệ Đột quỵ", f"{(filtered_df['Stroke'].mean()*100):.1f}%")
    c4.metric("Sức khỏe Tâm thần", f"{filtered_df['MentHlth'].mean():.1f} ngày", help="Số ngày thấy tệ trong 1 tháng")

    st.divider()

    # --- BIỂU ĐỒ ---
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Tình trạng Tiểu đường")
        fig_pie = px.pie(
            filtered_df, names='Diabetes_Status', 
            color='Diabetes_Status',
            color_discrete_map={'Khỏe mạnh': '#2A9D8F', 'Tiền tiểu đường': '#E9C46A', 'Tiểu đường': '#E76F51'},
            hole=0.5
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.subheader("Tương quan BMI theo Nhóm tuổi")
        # Sắp xếp lại thứ tự nhóm tuổi để biểu đồ không bị lộn xộn
        age_order = list(maps['Age_Label'].values())
        fig_box = px.box(
            filtered_df, x='Age_Range', y='BMI', 
            color='Diabetes_Status',
            category_orders={'Age_Range': age_order},
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        st.plotly_chart(fig_box, use_container_width=True)

    # --- THÓI QUEN SINH HOẠT ---
    st.subheader("Phân tích lối sống theo điều kiện sức khỏe")
    habit_cols = ['PhysActivity', 'Fruits', 'Veggies', 'Smoker', 'HvyAlcoholConsump']
    
    # Tính toán tỷ lệ %
    df_habit = filtered_df.groupby('Diabetes_Status')[habit_cols].mean() * 100
    df_habit.columns = ['Vận động', 'Ăn trái cây', 'Ăn rau', 'Hút thuốc', 'Uống rượu bia']
    
    st.bar_chart(df_habit.T)

    # --- DỮ LIỆU CHI TIẾT & DOWNLOAD ---
    with st.expander("Truy xuất dữ liệu thô (1,000 dòng đầu)"):
        # Nút Download dữ liệu đã lọc
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Tải xuống dữ liệu đã lọc (CSV)",
            data=csv,
            file_name='filtered_health_data.csv',
            mime='text/csv',
        )
        
        # Hiển thị dataframe có style
        st.dataframe(
            filtered_df.head(1000).style.background_gradient(subset=['BMI'], cmap='YlOrRd'),
            use_container_width=True
        )

if __name__ == "__main__":
    main()