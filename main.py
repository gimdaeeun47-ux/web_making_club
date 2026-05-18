import streamlit as st
import numpy as np
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="초대형 드론 추력 시뮬레이터", layout="wide", page_icon="🛸")

st.title("🛸 초대형 프로펠러 및 기후 반영 시뮬레이터")
st.markdown("최대 30m의 초대형 프로펠러 제원과 대기 온도가 추력 및 회전 물리 현상에 미치는 영향을 시뮬레이션합니다.")
st.markdown("---")

# 2. 사이드바 설정 (최대 길이 30m로 변경)
st.sidebar.header("⚙️ 시뮬레이션 제원 설정")

propeller_length = st.sidebar.slider(
    "📏 프로펠러 직경/길이 (m)",
    min_value=0.1, max_value=30.0, value=5.0, step=0.5
)

rpm = st.sidebar.slider(
    "🔄 모터 RPM 설정",
    min_value=0, max_value=10000, value=2000, step=100
)

temperature = st.sidebar.slider(
    "🌡️ 대기 온도 (°C)",
    min_value=-20, max_value=45, value=15, step=1
)

# 3. 물리 및 역학 계산
P_sea_level = 101325  
R_air = 287.05        
T_kelvin = temperature + 273.15  

# 공기 밀도 (kg/m³)
air_density = P_sea_level / (R_air * T_kelvin)
standard_density = 1.225 

# 추력 계산 (상수 보정)
n = rpm / 60
k_base = 0.0000001  
k_current = k_base * (air_density / standard_density)
thrust = k_current * (n ** 2) * (propeller_length ** 4)

# [핵심] 날개 끝단 속도(Tip Speed) 계산: V = ω * r
# RPM을 각속도(rad/s)로 바꾸고 반지름(Length / 2)을 곱함
tip_speed = (2 * np.pi * rpm / 60) * (propeller_length / 2)
mach_number = tip_speed / 340.0 # 음속(약 340m/s) 대비 비율

# 4. 애니메이션 동적 제어 (RPM과 길이에 모두 연동)
if rpm > 0:
    # 1) 회전 속도(초): RPM이 높을수록 빠르되, 길이가 길수록 거대한 관성을 표현하기 위해 주기 가중치 부여
    duration = (60 / rpm) * (1 + (propeller_length / 30.0) * 0.5)
    # 2) 잔상(Blur): 끝단 속도(tip_speed)가 빠를수록 공기 찢김 잔상이 강해짐
    blur_radius = min(15, (tip_speed / 50.0))
else:
    duration = 0
    blur_radius = 0

# 프로펠러 그래픽 크기 스케일링 (0.1m ~ 30m 대응 슬라이딩)
# 화면에서 완전히 사라지거나 삐져나가지 않도록 최소/최대 크기 제한
blade_visual_radius = 15 + 80 * (propeller_length / 30.0)
stroke_width = 4 + 14 * (propeller_length / 30.0)

# 음속 돌파 시 프로펠러 색상 변경 (시각적 피드백)
prop_color = "#EF4444" if mach_number >= 1.0 else "#F8FAFC"
hub_color = "#F59E0B" if mach_number >= 1.0 else "#0284C7"

# 5. 메인 레이아웃 구성
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("🌀 프로펠러 동적 물리 애니메이션")
    
    # CSS 애니메이션 및 SVG 동적 결합
    animation_style = f"animation: spin {duration}s linear infinite;" if rpm > 0 else ""
    blur_style = f"filter: blur({blur_radius}px);" if blur_radius > 1 else ""
    
    propeller_html = f"""
    <div style="display: flex; justify-content: center; align-items: center; height: 340px; background: #0F172A; border-radius: 16px; overflow: hidden;">
        <svg width="300" height="300" viewBox="0 0 200 200" style="{animation_style}">
            <style>
                @keyframes spin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
                transform-origin: center;
            </style>
            <!-- 1. 속도와 길이에 반응하는 공기 동역학적 잔상 레이어 -->
            <g style="{blur_style} opacity: 0.5;">
                <line x1="100" y1="{100 - blade_visual_radius}" x2="100" y2="{100 + blade_visual_radius}" stroke="{prop_color}" stroke-width="{stroke_width * 1.5}" stroke-linecap="round"/>
            </g>
            <!-- 2. 실제 프로펠러 날개 -->
            <line x1="100" y1="{100 - blade_visual_radius}" x2="100" y2="{100 + blade_visual_radius}" stroke="{prop_color}" stroke-width="{stroke_width}" stroke-linecap="round"/>
            <!-- 3. 중심축 회전 서브 로터 -->
            <line x1="{100 - blade_visual_radius*0.3}" y1="100" x2="{100 + blade_visual_radius*0.3}" y2="100" stroke="#64748B" stroke-width="{stroke_width*0.4}" stroke-linecap="round" opacity="0.6"/>
            <!-- 4. 모터 중심 허브 -->
            <circle cx="100" cy="100" r="{6 + stroke_width*0.3}" fill="{hub_color}"/>
            <circle cx="100" cy="100" r="3" fill="#1E293B"/>
        </svg>
    </div>
    """
    st.components.v1.html(propeller_html, height=350)
    
    # 음속 및 물리 경고 메세지 구역
    st.markdown("### 📢 물리적 상태 진단")
    if mach_number >= 1.0:
        st.error(f"💥 **소닉 붐 발생! 날개 끝단이 음속을 돌파했습니다.**\n\n현재 날개 끝 속도가 **{tip_speed:.1f} m/s (Mach {mach_number:.2f})**에 도달했습니다. 이 상태에서는 엄청난 소음과 함께 충격파가 발생하여 날개가 파괴되거나 효율이 극도로 저하됩니다. 실현 불가능한 설계입니다!")
    elif mach_number >= 0.7:
        st.warning(f"⚠️ **천음속 영역 진입 (충격파 위험)**\n\n끝단 속도가 **{tip_speed:.1f} m/s**로 음속의 70%를 넘었습니다. 소음이 극심해지며 프로펠러 효율 항력이 급증하는 구간입니다.")
    else:
        st.success(f"🟢 **안정적인 선속도 범위 보존**\n\n날개 끝단 속도가 **{tip_speed:.1f} m/s**로 안전 구역 내에 있습니다. 구조적으로 비행하기에 적합한 회전 속도입니다.")

with col2:
    st.subheader("📊 성능 및 기후 실시간 지표")
    
    # 지표 격자 배치
    m1, m2 = st.columns(2)
    with m1:
        st.metric(label="🧪 최종 계산 추력", value=f"{thrust:.4f} N")
        st.metric(label="💨 날개 끝단 선속도", value=f"{tip_speed:.1f} m/s", delta=f"Mach {mach_number:.2f}")
    with m2:
        st.metric(label="🌡️ 대기 밀도", value=f"{air_density:.3f} kg/m³")
        st.metric(label="📐 프로펠러 실제 거대함", value=f"{propeller_length:.1f} m", delta="최대 30m 세팅 적용 중")
        
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    
    # Plotly 시각화 (현재 작동점 및 추력 곡선)
    rpm_range = np.linspace(0, 10000, 100)
    thrust_range = k_current * ((rpm_range / 60) ** 2) * (propeller_length ** 4)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rpm_range, y=thrust_range,
        mode='lines', name='현재 환경 추력 곡선',
        line=dict(color='#10B981' if mach_number < 1.0 else '#EF4444', width=3)
    ))
    fig.add_trace(go.Scatter(
        x=[rpm], y=[thrust],
        mode='markers', name='현재 작동점',
        marker=dict(color='#3B82F6', size=14, line=dict(color='white', width=2))
    ))
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=10, b=20),
        height=240,
        hovermode="x unified",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title="RPM", gridcolor='#E2E8F0'),
        yaxis=dict(title="Thrust (N)", gridcolor='#E2E8F0'),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)