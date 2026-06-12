import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re

st.set_page_config(
    page_title="德国线上电子烟热销口味调研数据看板",
    page_icon="🇩🇪",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1a56db 0%, #1e429f 100%);
        padding: 16px 20px; border-radius: 12px; color: white;
        text-align: center; box-shadow: 0 4px 15px rgba(26,86,219,0.25);
    }
    .metric-card .value { font-size: 2rem; font-weight: 700; line-height: 1; }
    .metric-card .label { font-size: 0.8rem; opacity: 0.9; margin-top: 6px; }
    .section-title {
        font-size: 1.05rem; font-weight: 600; color: #1e3a5f;
        margin: 18px 0 10px 0; padding-left: 10px;
        border-left: 4px solid #1a56db;
    }
    .insight-box {
        background: #eff6ff; border-left: 4px solid #1a56db;
        padding: 12px 16px; border-radius: 0 8px 8px 0;
        margin: 8px 0; font-size: 0.92rem; line-height: 1.7;
    }
    .black-box {
        background: #fef3c7; border-left: 4px solid #d97706;
        padding: 12px 16px; border-radius: 0 8px 8px 0;
        margin: 8px 0; font-size: 0.92rem; line-height: 1.7;
    }
    .action-box {
        background: #f0fdf4; border-left: 4px solid #10b981;
        padding: 12px 16px; border-radius: 0 8px 8px 0;
        margin: 8px 0; font-size: 0.92rem; line-height: 1.7;
    }
    .tag-chip {
        display: inline-block; background: #dbeafe; color: #1e40af;
        padding: 2px 10px; border-radius: 999px;
        font-size: 0.78rem; margin: 2px;
    }
    .flavor-row {
        margin: 3px 0 6px 0; padding: 6px 10px;
        background: #f8fafc; border-radius: 6px;
        font-size: 0.85rem; color: #374151;
    }
    .summary-card {
        background: #f0fdf4; border-radius: 12px; padding: 16px;
        margin: 12px 0; border-left: 6px solid #10b981;
    }
    .warning-card {
        background: #fff7ed; border-radius: 12px; padding: 16px;
        margin: 12px 0; border-left: 6px solid #f97316;
    }
    .danger-card {
        background: #fef2f2; border-radius: 12px; padding: 16px;
        margin: 12px 0; border-left: 6px solid #ef4444;
    }
    .insight-tag {
        display: inline-block; background: #f0fdf4; color: #065f46;
        border: 1px solid #6ee7b7; padding: 2px 10px; border-radius: 999px;
        font-size: 0.78rem; margin: 2px;
    }
</style>
""", unsafe_allow_html=True)

COLORS = {
    "primary": "#1a56db", "secondary": "#1e429f",
    "black": "#d97706", "compliant": "#10b981",
    "china": "#ef4444", "germany": "#3b82f6",
    "uk": "#8b5cf6", "us": "#06b6d4",
    "sweden": "#f59e0b", "uae": "#14b8a6",
    "ice": "#38bdf8", "tobacco": "#92400e",
    "fruit": "#f59e0b", "sweet": "#ec4899",
    "drink": "#06b6d4", "candy": "#8b5cf6",
    "menthol": "#34d399", "other": "#94a3b8",
}
CAT_COLOR_MAP = {
    "水果": COLORS["fruit"], "烟草": COLORS["tobacco"],
    "甜点": COLORS["sweet"], "饮料": COLORS["drink"],
    "糖果": COLORS["candy"], "薄荷": COLORS["menthol"],
    "其他": COLORS["other"],
}
COUNTRY_COLOR_MAP = {
    "中国": COLORS["china"], "德国": COLORS["germany"],
    "英国": COLORS["uk"], "美国": COLORS["us"],
    "瑞典": COLORS["sweden"], "阿联酋": COLORS["uae"],
}
TYPE_COLOR_MAP = {
    "常规一次性/预注油Pod": COLORS["compliant"],
    "烟油": COLORS["primary"],
    "大口数一次性": COLORS["black"],
}
BLACK_BRANDS = {
    "Fumot":     {"product": "Randm Tornado 40000 / Leopard 40K", "color": "#ef4444"},
    "AL FAKHER": {"product": "30K Hypermax",                      "color": "#d97706"},
    "Vozol":     {"product": "Vista 40000",                       "color": "#8b5cf6"},
}
T = "plotly_white"

@st.cache_data
def load_data():
    df = pd.read_excel("Gemany-onlinedata-Erin-202606.xlsx", sheet_name="Sheet1")
    df.columns = df.columns.str.strip()
    df["含冰/薄荷"] = df["含冰/薄荷"].fillna("不确定")
    df["含烟草"] = df["含烟草"].fillna("否")

    def split_flavor_tags(tag_str):
        if pd.isna(tag_str):
            return []
        parts = [p.strip().lower() for p in str(tag_str).split(",") if p.strip()]
        return parts

    df["口味标签列表"] = df["口味标签"].apply(split_flavor_tags)

    def parse_price(p):
        if pd.isna(p): return None
        s = str(p).replace("\xa0", "").replace(",", ".")
        m = re.search(r"[\d\.]+", s)
        if m:
            try: return float(m.group())
            except: return None
        return None
    df["价格_数值"] = df["价格"].apply(parse_price)

    def nic_list(v):
        if pd.isna(v): return []
        nums = re.findall(r"\d+", str(v))
        return [int(x) for x in nums]
    df["尼古丁档位列表"] = df["尼古丁浓度mg"].apply(nic_list)
    df["尼古丁最高浓度"] = df["尼古丁档位列表"].apply(lambda l: max(l) if l else None)
    df["口味标签数"] = df["口味标签列表"].apply(len)

    def complexity(n):
        if n <= 1: return "单一口味"
        elif n == 2: return "双重复合"
        else: return "三重以上复合"
    df["口味复杂度"] = df["口味标签数"].apply(complexity)
    df["容量显示"] = df["容量ml"].astype(str)

    # 新增：性价比计算（大口数）
    def get_puffs(row):
        if row["产品类型"] != "大口数一次性": return None
        v = str(row["容量ml"])
        if "K" in v.upper():
            nums = re.findall(r"[\d\.]+", v)
            return float(nums[0]) * 1000 if nums else None
        nums = re.findall(r"\d+", v)
        return int(nums[0]) if nums else None
    df["puffs数值"] = df.apply(get_puffs, axis=1)
    df["性价比_puffs_per_euro"] = df["puffs数值"] / df["价格_数值"]

    # 新增：网站类型分类
    black_sites = {"fumot-store.de", "fumotvapepro.de", "randmvapes.net",
                   "vozol-evape.de", "vozolvapen.de", "aladin-shishashop.de",
                   "alfakher-official.de", "el-badia.com"}
    df["网站类型"] = df["网站名称"].apply(lambda x: "黑市专营" if x in black_sites else "综合零售")

    return df

df = load_data()

# 侧边栏筛选
with st.sidebar:
    st.markdown("## 🔍 筛选")
    st.markdown("---")
    sel_types = st.multiselect("产品类型", df["产品类型"].unique(), default=df["产品类型"].unique())
    sel_compliant = st.multiselect("合规性", ["是", "否"], default=["是", "否"])
    sel_cats = st.multiselect("口味分类", df["分类"].unique(), default=df["分类"].unique())
    sel_sites = st.multiselect("网站", df["网站名称"].unique(), default=df["网站名称"].unique())
    st.markdown("---")
    st.caption("📅 数据采集：2026-06")
    st.caption("数据看板制作人：Erin")
    st.caption(f"覆盖 {df['网站名称'].nunique()} 个网站 · {len(df)} 条记录")

fdf = df[
    df["产品类型"].isin(sel_types) &
    df["是否合规"].isin(sel_compliant) &
    df["分类"].isin(sel_cats) &
    df["网站名称"].isin(sel_sites)
].copy()

if fdf.empty:
    st.error("⚠️ 当前筛选条件下无数据，请放宽筛选范围。")
    st.stop()

st.markdown("# 🇩🇪 德国线上电子烟热销口味调研数据看板")
st.caption(
    f"筛选后：{len(fdf)} 条 ｜ 品牌 {fdf['品牌'].nunique()} 个 ｜ 网站 {fdf['网站名称'].nunique()} 个 ｜ 独立口味 {fdf['口味名称'].nunique()} 个"
)
st.markdown("---")

tabs = st.tabs([
    "📊 总览",
    "🖤 大口数三品牌",
    "🍭 口味热榜",
    "🔖 口味元素",
    "💉 尼古丁规格",
    "💰 价格与性价比",
    "🏷️ 品牌分析",
    "🌐 渠道结构",
    "🇩🇪 本土 vs 外来",
    "📝 总结洞察",
    "📋 原始数据",
])

# ========== TAB 0 总览 ==========
with tabs[0]:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    kpis = [
        ("总记录数",      len(fdf)),
        ("品牌数",        fdf["品牌"].nunique()),
        ("独立口味数",    fdf["口味名称"].nunique()),
        ("合规产品占比",  f"{(fdf['是否合规']=='是').sum()/len(fdf):.0%}"),
        ("含冰/薄荷占比", f"{(fdf['含冰/薄荷']=='是').sum()/len(fdf):.0%}"),
        ("覆盖网站数",    fdf["网站名称"].nunique()),
    ]
    for col, (label, val) in zip([c1, c2, c3, c4, c5, c6], kpis):
        col.markdown(
            f'<div class="metric-card"><div class="value">{val}</div><div class="label">{label}</div></div>',
            unsafe_allow_html=True
        )
    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown('<p class="section-title">口味分类分布</p>', unsafe_allow_html=True)
        cc = fdf["分类"].value_counts().reset_index()
        cc.columns = ["分类", "数量"]
        fig = px.bar(cc, x="分类", y="数量", color="分类",
                     color_discrete_map=CAT_COLOR_MAP, text="数量", template=T)
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False, margin=dict(t=10, b=10), xaxis_title="", yaxis_title="数量")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("水果口味占绝对主导（约74%），其次是饮料和薄荷，烟草和甜点占比极低。")

    with col_r:
        st.markdown('<p class="section-title">三大产品类型 × 口味分类</p>', unsafe_allow_html=True)
        cross = fdf.groupby(["产品类型", "分类"]).size().reset_index(name="数量")
        fig = px.bar(cross, x="产品类型", y="数量", color="分类",
                     barmode="stack", color_discrete_map=CAT_COLOR_MAP, template=T)
        fig.update_layout(xaxis_title="", yaxis_title="数量",
                          legend_title_text="分类", margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("本次热销调研中烟油是唯一包含烟草/甜点口味的品类；大口数产品口味结构与常规一次性和Pod高度趋同，以水果为主。")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<p class="section-title">数据来源品牌国构成</p>', unsafe_allow_html=True)
        oc = fdf["品牌来源国"].value_counts().reset_index()
        oc.columns = ["来源国", "数量"]
        fig = px.pie(oc, values="数量", names="来源国",
                     color="来源国", color_discrete_map=COUNTRY_COLOR_MAP,
                     hole=0.45, template=T)
        fig.update_traces(textposition="outside", textinfo="percent+label")
        fig.update_layout(margin=dict(t=20, b=20), legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("中国品牌占65%（数量），德国本土占17%，阿联酋品牌占10%但均价最高。")

    with col_b:
        st.markdown('<p class="section-title">口味复杂度（单一 vs 复合）</p>', unsafe_allow_html=True)
        comp = fdf["口味复杂度"].value_counts().reset_index()
        comp.columns = ["复杂度", "数量"]
        fig = px.pie(comp, values="数量", names="复杂度",
                     color="复杂度",
                     color_discrete_map={"单一口味": "#94a3b8", "双重复合": COLORS["primary"], "三重以上复合": COLORS["secondary"]},
                     hole=0.45, template=T)
        fig.update_traces(textposition="outside", textinfo="percent+label")
        fig.update_layout(margin=dict(t=20, b=20), legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("复合口味占比超过60%，市场偏好层次丰富的口感组合，单一口味产品市场空间收窄。")

    # 调研方法说明
    st.markdown("---")
    st.markdown('<p class="section-title">📋 调研覆盖范围说明</p>', unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("""
        <div class="black-box">
        <b>🖤 热销大口数品牌（3品牌×3网站×Top10）</b><br>
        • <b>Fumot</b> Randm Tornado 40000：fumot-store.de / fumotvapepro.de / randmvapes.net<br>
        • <b>AL FAKHER</b> 30K Hypermax：aladin-shishashop.de / alfakher-official.de / el-badia.com<br>
        • <b>Vozol</b> Vista 40000：vozol-evape.de / vozolvapen.de / fumot-store.de
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        st.markdown("""
        <div class="action-box">
        <b>✅ 常规合规一次性/预注油Pod（5网站×Top20）</b><br>
        • besserdampfen.de<br>
        • dampfdorado.de<br>
        • paradise-shisha.de<br>
        • steam-time.de<br>
        • vapebazar.de
        </div>
        """, unsafe_allow_html=True)
    with col_c:
        st.markdown("""
        <div class="insight-box">
        <b>🧴 常规合规烟油Liquid（5网站×Top20）</b><br>
        • besserdampfen.de<br>
        • dampfdorado.de<br>
        • paradise-shisha.de<br>
        • steam-time.de<br>
        • vapebazar.de
        </div>
        """, unsafe_allow_html=True)



# ========== TAB 1 黑市大口数三品牌 ==========
with tabs[1]:
    st.markdown("### 🖤 大口数单品牌口味调研")

    black_df = fdf[fdf["产品类型"] == "大口数一次性"].copy()
    if black_df.empty:
        st.info("当前筛选下无大口数数据，请在侧边栏中勾选「否」合规性。")
    else:
        # 三品牌KPI
        brand_cols = st.columns(3)
        for col, (brand, info) in zip(brand_cols, BLACK_BRANDS.items()):
            bdf = black_df[black_df["品牌"] == brand]
            if bdf.empty:
                continue
            ice_pct = (bdf["含冰/薄荷"] == "是").sum() / len(bdf)
            top_cat = bdf["分类"].value_counts().idxmax()
            avg_price = bdf["价格_数值"].mean()
            avg_puffs = bdf["puffs数值"].mean()
            ppe = bdf["性价比_puffs_per_euro"].mean()
            col.markdown(
                f'<div class="metric-card" style="background:linear-gradient(135deg,{info["color"]},#1e429f);">'
                f'<div class="value" style="font-size:1.3rem">{brand}</div>'
                f'<div class="label">{info["product"]}<br>'
                f'均价 €{avg_price:.2f} ｜ 含冰 {ice_pct:.0%}<br>'
                f'性价比 {ppe:,.0f} puffs/€</div></div>',
                unsafe_allow_html=True
            )
        st.markdown("<br>", unsafe_allow_html=True)

        # 均价对比
        st.markdown('<p class="section-title">⚡ 三品牌均价对比</p>', unsafe_allow_html=True)
        ppe_data = []
        for brand in BLACK_BRANDS:
            bdf2 = black_df[black_df["品牌"] == brand]
            if not bdf2.empty:
                avg_puffs = bdf2["puffs数值"].mean()
                avg_price = bdf2["价格_数值"].mean()
                ppe = bdf2["性价比_puffs_per_euro"].mean()
                ppe_data.append({"品牌": brand, "平均puffs": avg_puffs, "均价(€)": round(avg_price, 2), "性价比(puffs/€)": round(ppe, 0)})
        ppe_df = pd.DataFrame(ppe_data)
        fig_price_comp = px.bar(ppe_df, x="品牌", y="均价(€)", text="均价(€)",
                                color="品牌", color_discrete_map={b: i["color"] for b, i in BLACK_BRANDS.items()},
                                template=T)
        fig_price_comp.update_traces(texttemplate="€%{text:.2f}", textposition="outside")
        fig_price_comp.update_layout(showlegend=False, yaxis_title="均价（€）", xaxis_title="")
        st.plotly_chart(fig_price_comp, use_container_width=True)

        st.markdown("---")

        st.markdown('<p class="section-title">📊 综合热度 Top 10（基于排名权重 × 出现网站数）</p>', unsafe_allow_html=True)

        sel_brand = st.selectbox(
            "选择品牌",
            list(BLACK_BRANDS.keys()),
            format_func=lambda x: f"{x}  ·  {BLACK_BRANDS[x]['product']}"
        )

        brand_data = black_df[black_df["品牌"] == sel_brand].copy()
        if brand_data.empty:
            st.warning(f"未找到品牌 {sel_brand} 的大口数产品数据。")
        else:
            brand_data["排名_数值"] = pd.to_numeric(brand_data["排名"], errors="coerce")
            brand_data = brand_data.dropna(subset=["排名_数值"])

            flavor_scores = {}
            flavor_meta = {}
            for _, row in brand_data.iterrows():
                flavor = row["口味名称"]
                rank = row["排名_数值"]
                site = row["网站名称"]
                ice_flag = row["含冰/薄荷"]
                tags = row["口味标签列表"]
                score_inc = 1.0 / rank

                if flavor not in flavor_scores:
                    flavor_scores[flavor] = 0.0
                    flavor_meta[flavor] = {
                        "sites": set(),
                        "ice": ice_flag == "是",
                        "tags": tags,
                        "occurrences": 0,
                        "best_rank": rank,
                        "sum_inv_rank": 0.0
                    }
                flavor_scores[flavor] += score_inc
                flavor_meta[flavor]["sites"].add(site)
                flavor_meta[flavor]["occurrences"] += 1
                flavor_meta[flavor]["sum_inv_rank"] += score_inc
                if rank < flavor_meta[flavor]["best_rank"]:
                    flavor_meta[flavor]["best_rank"] = rank

            final_scores = {f: score * len(flavor_meta[f]["sites"]) for f, score in flavor_scores.items()}

            top_flavors = pd.DataFrame([
                {
                    "口味名称": f,
                    "综合得分": round(final_scores[f], 4),
                    "出现网站数": len(flavor_meta[f]["sites"]),
                    "总上榜次数": flavor_meta[f]["occurrences"],
                    "最佳排名": int(flavor_meta[f]["best_rank"]),
                    "含冰/薄荷": "是" if flavor_meta[f]["ice"] else "否",
                    "口味标签": ", ".join(flavor_meta[f]["tags"][:3]) if flavor_meta[f]["tags"] else "-"
                }
                for f in final_scores
            ]).sort_values("综合得分", ascending=False).head(10)

            st.markdown(
                '<div class="insight-box">📐 <b>权重算法说明：</b> 综合得分 = Σ(1/排名) × 出现网站数。<br>'
                '其中 Σ(1/排名) 是口味在各个网站榜单中排名倒数的累加和（排名越前贡献越大），'
                '再乘以该口味出现的不同网站数量，既重视榜单名次，也强调在多个网站同时热销。</div>',
                unsafe_allow_html=True
            )

            fig_top = px.bar(
                top_flavors,
                x="综合得分",
                y="口味名称",
                orientation="h",
                text="综合得分",
                color="综合得分",
                color_continuous_scale=[[0, "#fef3c7"], [1, BLACK_BRANDS[sel_brand]["color"]]],
                template=T,
                category_orders={"口味名称": top_flavors["口味名称"].tolist()}
            )
            fig_top.update_traces(texttemplate='%{text:.4f}', textposition="outside")
            fig_top.update_layout(
                height=450,
                xaxis_title="综合得分 (∑1/排名 × 网站数)",
                yaxis_title="",
                yaxis={'categoryorder':'total ascending'},
                coloraxis_showscale=False,
                margin=dict(t=10, b=10)
            )
            st.plotly_chart(fig_top, use_container_width=True)

            st.dataframe(
                top_flavors,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "口味名称": "口味",
                    "综合得分": st.column_config.NumberColumn("综合得分", format="%.4f"),
                    "出现网站数": "覆盖网站数",
                    "总上榜次数": "总上榜次数",
                    "最佳排名": "最高名次",
                    "含冰/薄荷": "冰感",
                    "口味标签": "主要标签"
                }
            )

            with st.expander("🔎 点击查看每个口味的详细来源网站"):
                for _, row in top_flavors.iterrows():
                    flavor = row["口味名称"]
                    sites = flavor_meta[flavor]["sites"]
                    st.markdown(f"**{flavor}** → 出现网站：{', '.join(sites)}")

            st.markdown("---")

        # 三品牌口味元素对比热图
        st.markdown('<p class="section-title">三品牌口味元素对比热图</p>', unsafe_allow_html=True)
        all_b_tags = []
        for tl in black_df["口味标签列表"]: all_b_tags.extend(tl)
        top15 = [t for t, _ in Counter(all_b_tags).most_common(15)]

        brand_tag_matrix = {}
        for brand in BLACK_BRANDS:
            bdf2 = black_df[black_df["品牌"] == brand]
            btags = []
            for tl in bdf2["口味标签列表"]: btags.extend(tl)
            brand_tag_matrix[brand] = Counter(btags)

        matrix_df = pd.DataFrame(
            {brand: [brand_tag_matrix[brand].get(t, 0) for t in top15] for brand in BLACK_BRANDS},
            index=top15
        )
        fig = px.imshow(matrix_df.T, text_auto=True, aspect="auto",
                        color_continuous_scale=[[0, "#fef3c7"], [1, "#d97706"]], template=T)
        fig.update_layout(xaxis_title="", yaxis_title="",
                          coloraxis_showscale=False, height=220, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        common = set.intersection(*[set(brand_tag_matrix[b].keys()) for b in BLACK_BRANDS])
        if common:
            top_common = sorted(common, key=lambda t: sum(brand_tag_matrix[b].get(t, 0) for b in BLACK_BRANDS), reverse=True)
            st.markdown(
                '<div class="black-box"><b>🎯 三品牌共同出现的口味元素：</b><br>' +
                " ".join([f'<span class="tag-chip">{t}</span>' for t in top_common]) +
                "</div>", unsafe_allow_html=True
            )
            st.caption("冰、莓果、热带水果是大口数品牌共同主推的元素。")

# ========== TAB 2 口味热榜 ==========
with tabs[2]:
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown('<p class="section-title">全榜热门口味 Top 15</p>', unsafe_allow_html=True)
        flavor_counts = fdf["口味名称"].value_counts()
        fl = flavor_counts.head(15).reset_index()
        fl.columns = ["口味名称", "出现次数"]
        fl = fl.sort_values("出现次数", ascending=True)
        fig = px.bar(fl, x="出现次数", y="口味名称", orientation="h",
                     text="出现次数", color_discrete_sequence=[COLORS["primary"]], template=T)
        fig.update_traces(textposition="outside")
        fig.update_layout(height=480, margin=dict(t=10, b=10), xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

        if not flavor_counts.empty:
            top1_cnt = flavor_counts.iloc[0]
            top1_flavors = flavor_counts[flavor_counts == top1_cnt].index.tolist()
            second_cnt = flavor_counts[flavor_counts < top1_cnt].iloc[0] if (flavor_counts < top1_cnt).any() else None
            second_flavors = flavor_counts[flavor_counts == second_cnt].index.tolist() if second_cnt is not None else []
            cap = f"全市场最热门的口味为：{', '.join(top1_flavors)}，出现次数最高达 {top1_cnt} 次。"
            if second_flavors:
                cap += f"第二名共有{len(second_flavors)}个口味并列，出现次数均为 {second_cnt} 次，分别是：{', '.join(second_flavors)}。"
            st.caption(cap)

    with col_r:
        st.markdown('<p class="section-title">按产品类型查看 Top 15</p>', unsafe_allow_html=True)
        ptype = st.selectbox("选择产品类型", fdf["产品类型"].unique(), key="tab2_type")
        tfl_counts = fdf[fdf["产品类型"] == ptype]["口味名称"].value_counts()
        tfl = tfl_counts.head(15).reset_index()
        tfl.columns = ["口味名称", "出现次数"]
        tfl = tfl.sort_values("出现次数", ascending=True)
        fig = px.bar(tfl, x="出现次数", y="口味名称", orientation="h", text="出现次数",
                     color_discrete_sequence=[TYPE_COLOR_MAP.get(ptype, COLORS["primary"])], template=T)
        fig.update_traces(textposition="outside")
        fig.update_layout(height=480, margin=dict(t=10, b=10), xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    # 新增：口味跨产品类型热力图
    st.markdown('<p class="section-title">🔥 口味跨产品类型覆盖热力图（Top 20 口味）</p>', unsafe_allow_html=True)
    if fdf["产品类型"].nunique() >= 2:
        ftm = pd.crosstab(fdf["口味名称"], fdf["产品类型"])
        top20_flavors = fdf["口味名称"].value_counts().head(20).index
        ftm_top = ftm.loc[ftm.index.isin(top20_flavors)]
        if not ftm_top.empty:
            fig = px.imshow(ftm_top, text_auto=True, aspect="auto",
                            color_continuous_scale="Blues", template=T)
            fig.update_layout(xaxis_title="", yaxis_title="",
                              coloraxis_showscale=False, height=500, margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
            multi = ftm_top[ftm_top.sum(axis=1) >= 2]
            if not multi.empty:
                st.caption(f"共 {len(multi)} 个口味同时出现在2种以上产品类型中，如 Blueberry Sour Raspberry、Blue Razz Lemonade 等，是跨品类经典口味。")

    st.markdown('<p class="section-title">Top 15 口味详细标签</p>', unsafe_allow_html=True)
    fl_list = flavor_counts.head(15).reset_index()
    fl_list.columns = ["口味名称", "出现次数"]
    cols2 = st.columns(2)
    for i, (_, row) in enumerate(fl_list.iterrows()):
        fname = row["口味名称"]
        tag_freq = Counter([t for tl in fdf[fdf["口味名称"] == fname]["口味标签列表"] for t in tl])
        tags_html = " ".join([f'<span class="tag-chip">{t}</span>' for t, _ in tag_freq.most_common()]) \
                    or '<span style="color:#9ca3af">无标签</span>'
        with cols2[i % 2]:
            st.markdown(f'<div class="flavor-row"><b>#{i+1} {fname}</b>（{row["出现次数"]}次）<br>{tags_html}</div>',
                        unsafe_allow_html=True)

# ========== TAB 3 口味元素 ==========
with tabs[3]:
    all_tags = [t for tl in fdf["口味标签列表"] for t in tl]
    tag_counts = Counter(all_tags)

    st.markdown('<p class="section-title">高频口味元素 Top 20</p>', unsafe_allow_html=True)
    top_tags_df = pd.DataFrame(tag_counts.most_common(20), columns=["口味元素", "出现次数"])
    top_tags_df = top_tags_df.sort_values("出现次数", ascending=True)
    fig = px.bar(top_tags_df, x="出现次数", y="口味元素", orientation="h", text="出现次数",
                 color="出现次数", color_continuous_scale=[[0, "#dbeafe"], [1, COLORS["primary"]]], template=T)
    fig.update_traces(textposition="outside")
    fig.update_layout(coloraxis_showscale=False, height=540,
                      margin=dict(t=10, b=10), xaxis_title="", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    if tag_counts:
        top3_elems = [f"{t} ({c})" for t, c in tag_counts.most_common(3)]
        st.caption(f"出现频率最高的口味元素为：{', '.join(top3_elems)}，ice是最强信号元素。")

    st.markdown('<p class="section-title">合规 VS 不合规 口味元素对比（Top 12）</p>', unsafe_allow_html=True)
    tag_compare = []
    for origin, label in [("是", "✅ 合规"), ("否", "⚠️ 不合规")]:
        otags = [t for tl in fdf[fdf["是否合规"] == origin]["口味标签列表"] for t in tl]
        for t, c in Counter(otags).most_common(12):
            tag_compare.append({"口味元素": t, "出现次数": c, "合规性": label})
    tc_df = pd.DataFrame(tag_compare)
    if not tc_df.empty:
        fig = px.bar(tc_df, x="口味元素", y="出现次数", color="合规性", barmode="group",
                     color_discrete_map={"✅ 合规": COLORS["compliant"], "⚠️ 不合规": COLORS["black"]},
                     template=T)
        fig.update_layout(xaxis_title="", yaxis_title="", xaxis_tickangle=-30,
                          legend_title_text="", margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("所有产品在冰(Ice)、蓝莓(blueberry)、草莓(strawberry)的频率均很高；不合规产品中mango/passion fruit和blue raspberry等占比显著更高。")

    st.markdown('<p class="section-title">各口味分类高频元素</p>', unsafe_allow_html=True)
    cats = fdf["分类"].value_counts().index.tolist()
    cat_cols = st.columns(2)
    for i, cat in enumerate(cats):
        cdf = fdf[fdf["分类"] == cat]
        cat_tags_list = [t for tl in cdf["口味标签列表"] for t in tl]
        top6 = Counter(cat_tags_list).most_common(6)
        with cat_cols[i % 2]:
            st.markdown(
                f'<div class="flavor-row"><b>{cat}</b>（{len(cdf)}款）　' +
                " ".join([f'<span class="tag-chip">{t} {c}</span>' for t, c in top6]) +
                "</div>",
                unsafe_allow_html=True
            )

    # 新增：口味元素共现分析
    st.markdown('<p class="section-title">🔗 口味元素组合频率（Top 15 双元素组合）</p>', unsafe_allow_html=True)
    combos = Counter()
    for tl in fdf["口味标签列表"]:
        uniq = list(set(tl))
        for i in range(len(uniq)):
            for j in range(i+1, len(uniq)):
                pair = tuple(sorted([uniq[i], uniq[j]]))
                combos[pair] += 1
    top_combos = combos.most_common(15)
    combo_df = pd.DataFrame([(f"{a} + {b}", c) for (a,b), c in top_combos], columns=["组合", "出现次数"])
    combo_df = combo_df.sort_values("出现次数", ascending=True)
    fig_combo = px.bar(combo_df, x="出现次数", y="组合", orientation="h", text="出现次数",
                       color="出现次数", color_continuous_scale=[[0, "#dbeafe"], [1, "#7c3aed"]], template=T)
    fig_combo.update_traces(textposition="outside")
    fig_combo.update_layout(coloraxis_showscale=False, height=420, margin=dict(t=10, b=10))
    st.plotly_chart(fig_combo, use_container_width=True)
    st.caption("blueberry+raspberry是最高频的黄金组合。")

# ========== TAB 4 尼古丁规格 ==========
with tabs[4]:
    st.markdown("### 💉 尼古丁浓度分布")

    pod_df = fdf[fdf["产品类型"] == "常规一次性/预注油Pod"]
    liq_df = fdf[fdf["产品类型"] == "烟油"]
    blk_df = fdf[fdf["产品类型"] == "大口数一次性"]

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown('<p class="section-title">合规Pod（德国TPD上限20mg）</p>', unsafe_allow_html=True)
        if not pod_df.empty:
            pod_nic = pod_df["尼古丁最高浓度"].value_counts().reset_index()
            pod_nic.columns = ["浓度(mg)", "产品数"]
            fig = px.bar(pod_nic, x="浓度(mg)", y="产品数", text="产品数",
                         color_discrete_sequence=[COLORS["compliant"]], template=T)
            fig.update_traces(textposition="outside")
            fig.update_layout(margin=dict(t=10, b=10), xaxis_title="尼古丁浓度(mg)", yaxis_title="产品数")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("合规Pod几乎全部为20mg盐尼古丁，是欧盟TPD规定的最高限量，说明德国合规市场已高度标准化。")
        else:
            st.info("无合规Pod数据")

    with col_b:
        st.markdown('<p class="section-title">烟油Liquid常见浓度档位</p>', unsafe_allow_html=True)
        if not liq_df.empty:
            liq_nic_flat = [n for nlist in liq_df["尼古丁档位列表"] for n in nlist]
            liq_nic_df = pd.DataFrame(Counter(liq_nic_flat).items(), columns=["浓度(mg)", "出现次数"])
            liq_nic_df = liq_nic_df.sort_values("浓度(mg)")
            fig = px.bar(liq_nic_df, x="浓度(mg)", y="出现次数", text="出现次数",
                         color_discrete_sequence=[COLORS["primary"]], template=T)
            fig.update_traces(textposition="outside")
            fig.update_layout(margin=dict(t=10, b=10), xaxis_title="尼古丁浓度(mg)", yaxis_title="提供该档位的产品数")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("烟油产品提供0-20mg多档选择，0mg无尼古丁产品也有市场，满足逐步减量用户需求。")
        else:
            st.info("无烟油数据")

    with col_c:
        st.markdown('<p class="section-title">大口数尼古丁浓度</p>', unsafe_allow_html=True)
        if not blk_df.empty:
            blk_nic = blk_df["尼古丁最高浓度"].dropna().value_counts().reset_index()
            if not blk_nic.empty:
                blk_nic.columns = ["浓度(mg)", "产品数"]
                blk_nic = blk_nic.sort_values("浓度(mg)")
                fig = px.bar(blk_nic, x="浓度(mg)", y="产品数", text="产品数",
                             color_discrete_sequence=[COLORS["black"]], template=T)
                fig.update_traces(textposition="outside")
                fig.update_layout(margin=dict(t=10, b=10), xaxis_title="尼古丁浓度(mg)", yaxis_title="产品数")
                st.plotly_chart(fig, use_container_width=True)
                st.caption("大口数产品以50mg尼古丁为主（Fumot/Vozol），或6mg尼古丁（AL FAKHER合规化2+20组装一次性），策略分化明显。")
            else:
                st.info("无浓度数据")
        else:
            st.info("无大口数数据")

    st.markdown('<p class="section-title">三类产品尼古丁浓度对比</p>', unsafe_allow_html=True)
    nic_rows = []
    for _, row in fdf.iterrows():
        for n in row["尼古丁档位列表"]:
            nic_rows.append({"产品类型": row["产品类型"], "尼古丁浓度(mg)": n})
    nic_long = pd.DataFrame(nic_rows)
    if not nic_long.empty:
        fig = px.box(nic_long, x="产品类型", y="尼古丁浓度(mg)", color="产品类型",
                     color_discrete_map=TYPE_COLOR_MAP, points="all", template=T)
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="尼古丁浓度(mg)",
                          margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("烟油浓度分布最宽（0-20mg），大口数出现50mg超高浓度，合规Pod全部锁定在20mg顶格。")

    if "设备类别" in fdf.columns:
        st.markdown('<p class="section-title">📱 不同设备类别的尼古丁浓度分布</p>', unsafe_allow_html=True)
        device_nic = []
        for _, row in fdf.iterrows():
            for n in row["尼古丁档位列表"]:
                device_nic.append({"设备类别": row["设备类别"], "尼古丁浓度(mg)": n})
        dev_df = pd.DataFrame(device_nic)
        if not dev_df.empty:
            fig_dev = px.box(dev_df, x="设备类别", y="尼古丁浓度(mg)", color="设备类别",
                             points="all", template=T)
            fig_dev.update_layout(xaxis_title="", xaxis_tickangle=-20, showlegend=False)
            st.plotly_chart(fig_dev, use_container_width=True)
            st.caption("换弹Pod和一次性通常锁定20mg，瓶装油通常在0-20mg之间，Pod换弹2+20为了合规定在6mg。")

# ========== TAB 5 价格与性价比 ==========
with tabs[5]:
    price_df = fdf.dropna(subset=["价格_数值"])
    if price_df.empty:
        st.info("暂无价格数据。")
    else:
        price_cols = st.columns(len(fdf["产品类型"].unique()))
        for col, ptype in zip(price_cols, fdf["产品类型"].unique()):
            sub = price_df[price_df["产品类型"] == ptype]["价格_数值"]
            if not sub.empty:
                col.markdown(
                    f'<div class="metric-card"><div class="value">€{sub.mean():.2f}</div>'
                    f'<div class="label">{ptype} 均价<br>（€{sub.min():.0f}~€{sub.max():.0f}）</div></div>',
                    unsafe_allow_html=True
                )
        st.markdown("<br>", unsafe_allow_html=True)

        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown('<p class="section-title">各产品类型价格分布</p>', unsafe_allow_html=True)
            fig = px.box(price_df, x="产品类型", y="价格_数值", color="产品类型",
                         color_discrete_map=TYPE_COLOR_MAP, points="all", template=T)
            fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="价格（€）",
                              margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
            st.caption("大口数一次性均价€17.7，是合规Pod（€7.7）的2.3倍。")

        with col_r:
            st.markdown('<p class="section-title">🌍 各品牌来源国均价对比</p>', unsafe_allow_html=True)
            country_price = price_df.groupby("品牌来源国")["价格_数值"].mean().reset_index()
            country_price = country_price.sort_values("价格_数值", ascending=False)
            fig_cp = px.bar(country_price, x="品牌来源国", y="价格_数值", text="价格_数值",
                            color="品牌来源国", color_discrete_map=COUNTRY_COLOR_MAP,
                            template=T)
            fig_cp.update_traces(texttemplate='€%{text:.2f}', textposition="outside")
            fig_cp.update_layout(xaxis_title="", yaxis_title="平均价格（€）", showlegend=False)
            st.plotly_chart(fig_cp, use_container_width=True)
            st.caption("阿联酋品牌（AL FAKHER）均价€22.9最高，中国品牌均价相对较低，德国本土品牌均价中等（含瓶装油）。")

        st.markdown('<p class="section-title">价格 vs 排名关系</p>', unsafe_allow_html=True)
        fig = px.scatter(price_df, x="排名", y="价格_数值", color="产品类型",
                         hover_data=["品牌", "口味名称", "网站名称"],
                         color_discrete_map=TYPE_COLOR_MAP, template=T)
        fig.update_layout(xaxis_title="榜单排名", yaxis_title="价格（€）",
                          legend_title_text="", margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("价格与排名无明显相关性，口味/品牌认知是更核心的驱动因素。")

# ========== TAB 6 品牌分析 ==========
with tabs[6]:
    st.markdown("## 🏷️ 品牌维度分析")

    brand_counts = fdf["品牌"].value_counts().reset_index()
    brand_counts.columns = ["品牌", "产品数"]
    top_brands = brand_counts.head(10).sort_values("产品数", ascending=False)
    fig = px.bar(top_brands, x="产品数", y="品牌", orientation="h", text="产品数",
                 color="产品数", color_continuous_scale=[[0, "#dbeafe"], [1, COLORS["primary"]]],
                 template=T, category_orders={"品牌": top_brands["品牌"].tolist()})
    fig.update_traces(textposition="outside")
    fig.update_layout(coloraxis_showscale=False, height=450, margin=dict(t=10, b=10),
                      yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    st.caption("本次热销数据调研中：Elf Bar 以100个SKU遥遥领先，占全样本34%，是德国合规市场中的绝对强势品牌；挑选大口数品牌Vozol、Fumot、AL FAKHER作为“黑市”样本作为对照组口味调研。")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<p class="section-title">品牌来源国分布（品牌数）</p>', unsafe_allow_html=True)
        country_brand = fdf.groupby("品牌来源国")["品牌"].nunique().reset_index()
        country_brand.columns = ["来源国", "品牌数"]
        fig = px.pie(country_brand, values="品牌数", names="来源国",
                     color="来源国", color_discrete_map=COUNTRY_COLOR_MAP,
                     hole=0.45, template=T)
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("本次样本出现的品牌来源最多的TOP3国家为：德国、中国、英国；德国本土品牌全部集中在烟油品类，无一涉足一次性设备。")

    with col2:
        price_df_br = fdf.dropna(subset=["价格_数值"])
        price_by_brand = price_df_br.groupby("品牌")["价格_数值"].mean().reset_index()
        price_by_brand = price_by_brand.sort_values("价格_数值", ascending=False).head(15)
        fig = px.bar(price_by_brand, x="价格_数值", y="品牌", orientation="h", text="价格_数值",
                     color="价格_数值", color_continuous_scale=[[0, "#dbeafe"], [1, COLORS["primary"]]],
                     template=T, category_orders={"品牌": price_by_brand["品牌"].tolist()})
        fig.update_traces(texttemplate='€%{text:.2f}', textposition="outside")
        fig.update_layout(coloraxis_showscale=False, height=500, margin=dict(t=10, b=10),
                          yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        st.caption("AL FAKHER均价最高；Elf Bar均价€7.9；Fumot Randm均价€15.7，性价比高于AL FAKHER。")

    # 品牌口味偏好
    st.markdown('<p class="section-title">品牌代表性口味</p>', unsafe_allow_html=True)
    brand_choice = st.selectbox("选择品牌查看其热门口味", fdf["品牌"].unique())
    brand_flavors = fdf[fdf["品牌"] == brand_choice]["口味名称"].value_counts().head(8).reset_index()
    brand_flavors.columns = ["口味名称", "出现次数"]
    if not brand_flavors.empty:
        brand_flavors = brand_flavors.sort_values("出现次数", ascending=True)
        fig = px.bar(brand_flavors, x="出现次数", y="口味名称", orientation="h", text="出现次数",
                     color_discrete_sequence=[COLORS["primary"]], template=T,
                     category_orders={"口味名称": brand_flavors["口味名称"].tolist()})
        fig.update_traces(textposition="outside")
        fig.update_layout(height=400, margin=dict(t=10, b=10), yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

    # 品牌设备类型分布
    st.markdown('<p class="section-title">品牌设备类型分布</p>', unsafe_allow_html=True)
    device_by_brand = fdf.groupby(["品牌", "设备类别"]).size().reset_index(name="产品数")
    top_dev_brands = device_by_brand.groupby("品牌")["产品数"].sum().reset_index().sort_values("产品数", ascending=False).head(10)["品牌"].tolist()
    device_top = device_by_brand[device_by_brand["品牌"].isin(top_dev_brands)]
    fig = px.bar(device_top, x="品牌", y="产品数", color="设备类别", barmode="stack",
                 color_discrete_map={"换弹Pod": COLORS["compliant"], "一次性": COLORS["primary"],
                                     "瓶装油": COLORS["secondary"], "大口数一次性": COLORS["black"], "Pod换弹2+20": "#8b5cf6"},
                 template=T)
    fig.update_layout(xaxis_title="", yaxis_title="产品数量", xaxis_tickangle=-30,
                      legend_title_text="设备类别")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("本次热销样本中Elf Bar以换弹Pod为主力，同时涉足瓶装油；德国本土品牌专注瓶装油。")

# ========== TAB 7 渠道结构 ==========
with tabs[7]:
    st.markdown("## 🌐 渠道结构分析")

    st.markdown(
        '<div class="insight-box">本数据集覆盖 <b>13个有TOPSELLER/BESTSELLER/POPULAR榜单的德国电商网站</b>：其中5个综合零售商（besserdampfen、dampfdorado、paradise-shisha、steam-time、vapebazar）'
        '各采集了合规Pod+烟油共40条数据；8个有售卖大口数的专营网站（品牌官方或代理站）各采集大口数一次性10-20条数据，最终取每个网站品牌TOP10条数据。'
        '渠道高度分化，综合渠道与黑市渠道互不重叠。</div>',
        unsafe_allow_html=True
    )

    # 综合零售商口味偏好对比
    st.markdown('<p class="section-title">🛒 五大综合零售商口味分类偏好对比</p>', unsafe_allow_html=True)
    retail_sites = ["besserdampfen.de", "dampfdorado.de", "paradise-shisha.de", "steam-time.de", "vapebazar.de"]
    retail_df = fdf[fdf["网站名称"].isin(retail_sites)]
    if not retail_df.empty:
        site_cat = pd.crosstab(retail_df["网站名称"], retail_df["分类"])
        fig_sc = px.imshow(site_cat, text_auto=True, aspect="auto",
                           color_continuous_scale=[[0, "#eff6ff"], [1, COLORS["primary"]]], template=T)
        fig_sc.update_layout(xaxis_title="", yaxis_title="",
                             coloraxis_showscale=False, height=280, margin=dict(t=10, b=10))
        st.plotly_chart(fig_sc, use_container_width=True)
        st.caption("五大综合零售商口味结构高度相似，水果主导地位稳固；dampfdorado在烟草口味上投入更多。")

    # 各网站Top 5口味
    st.markdown('<p class="section-title">各网站热销 Top 5 口味</p>', unsafe_allow_html=True)
    site_sel = st.selectbox("选择网站", fdf["网站名称"].unique(), key="site_top5")
    site_top = fdf[fdf["网站名称"] == site_sel]["口味名称"].value_counts().head(5).reset_index()
    site_top.columns = ["口味名称", "出现次数"]
    if not site_top.empty:
        site_top = site_top.sort_values("出现次数", ascending=True)
        fig_st5 = px.bar(site_top, x="出现次数", y="口味名称", orientation="h", text="出现次数",
                         color_discrete_sequence=[COLORS["primary"]], template=T,
                         category_orders={"口味名称": site_top["口味名称"].tolist()})
        fig_st5.update_traces(textposition="outside")
        fig_st5.update_layout(height=300, margin=dict(t=10, b=10), yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_st5, use_container_width=True)


# ========== TAB 8 本土 vs 外来 ==========
with tabs[8]:
    st.markdown("## 🇩🇪 德国本土品牌 vs 外来品牌深度对比")

    st.markdown(
        '<div class="insight-box"><b>德国本土品牌：</b> Dampfdorado、ZAZO、Herrlan、5EL、KAFFEEPAUSE、HAYVAN JUICE、ANTIMATTER 等7个品牌，共49个SKU，<b>全部为瓶装烟油</b>。<br>'
        '<b>外来品牌（合规产品）：</b>中国（Elf Bar等）、美国（Vuse等）、英国（DINNER LADY等）、瑞典（MUST HAVE），共140个合规SKU，覆盖Pod+烟油+黑市设备。</div>',
        unsafe_allow_html=True
    )

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown('<p class="section-title">本土 vs 外来品牌：口味分类分布</p>', unsafe_allow_html=True)
        origin_cat = fdf.groupby(["是否德国本土品牌", "分类"]).size().reset_index(name="数量")
        origin_cat["来源"] = origin_cat["是否德国本土品牌"].map({"是": "🇩🇪 德国本土", "否": "🌍 外来品牌"})
        fig_oc = px.bar(origin_cat, x="分类", y="数量", color="来源",
                        barmode="group", template=T,
                        color_discrete_map={"🇩🇪 德国本土": COLORS["germany"], "🌍 外来品牌": COLORS["china"]})
        fig_oc.update_layout(xaxis_title="", yaxis_title="产品数", legend_title_text="")
        st.plotly_chart(fig_oc, use_container_width=True)
        st.caption("德国本土品牌在烟草（7款）上占比远高于外来品牌，体现本土品牌口味深化的差异化。")

    with col_r:
        st.markdown('<p class="section-title">本土 vs 外来品牌：冰感占比</p>', unsafe_allow_html=True)
        ice_origin = []
        for flag, label in [("是", "🇩🇪 德国本土"), ("否", "🌍 外来品牌")]:
            sub = fdf[fdf["是否德国本土品牌"] == flag]
            ice_cnt = (sub["含冰/薄荷"] == "是").sum()
            total = len(sub)
            ice_origin.append({"来源": label, "含冰": "是", "比例": ice_cnt/total if total>0 else 0})
            ice_origin.append({"来源": label, "含冰": "否/不确定", "比例": 1 - ice_cnt/total if total>0 else 0})
        ice_orig_df = pd.DataFrame(ice_origin)
        fig_io = px.bar(ice_orig_df, x="来源", y="比例", color="含冰", barmode="stack",
                        color_discrete_map={"是": COLORS["ice"], "否/不确定": "#9ca3af"},
                        text_auto='.0%', template=T)
        fig_io.update_layout(yaxis_title="占比", xaxis_title="")
        st.plotly_chart(fig_io, use_container_width=True)
        st.caption("外来品牌（含黑市）冰感比例显与德国本土烟油品牌冰感比例差别不大。")

    # 本土烟油 vs 外来烟油口味标签对比
    st.markdown('<p class="section-title">🏷️ 本土烟油 vs 外来烟油口味标签对比</p>', unsafe_allow_html=True)
    liq = fdf[fdf["产品类型"] == "烟油"].copy()
    local_liq_tags = [t for tl in liq[liq["是否德国本土品牌"] == "是"]["口味标签列表"] for t in tl]
    foreign_liq_tags = [t for tl in liq[liq["是否德国本土品牌"] == "否"]["口味标签列表"] for t in tl]
    top_tags_all = [t for t, _ in Counter(local_liq_tags + foreign_liq_tags).most_common(12)]
    liq_tag_cmp = []
    for t in top_tags_all:
        liq_tag_cmp.append({"标签": t, "出现次数": Counter(local_liq_tags).get(t, 0), "来源": "🇩🇪 本土烟油"})
        liq_tag_cmp.append({"标签": t, "出现次数": Counter(foreign_liq_tags).get(t, 0), "来源": "🌍 外来烟油"})
    liq_tag_df = pd.DataFrame(liq_tag_cmp)
    fig_ltc = px.bar(liq_tag_df, x="标签", y="出现次数", color="来源", barmode="group",
                     color_discrete_map={"🇩🇪 本土烟油": COLORS["germany"], "🌍 外来烟油": COLORS["china"]},
                     template=T)
    fig_ltc.update_layout(xaxis_title="", xaxis_tickangle=-30, yaxis_title="出现次数", legend_title_text="")
    st.plotly_chart(fig_ltc, use_container_width=True)
    st.caption("外来烟油以blueberry、strawberry等国际主流水果为主；德国本土烟油在tobacco、Ice、mint等传统元素上布局更多，同时也有自己的水果系列。")

    # 本土品牌列表和详情
    st.markdown('<p class="section-title">🇩🇪 德国本土品牌概览</p>', unsafe_allow_html=True)
    local_brands = fdf[fdf["是否德国本土品牌"] == "是"].groupby("品牌").agg(
        产品数=("口味名称", "count"),
        独立口味=("口味名称", "nunique"),
        主要分类=("分类", lambda x: x.value_counts().idxmax()),
        均价=("价格_数值", "mean"),
        冰感占比=("含冰/薄荷", lambda x: f"{(x=='是').mean():.0%}")
    ).reset_index().sort_values("产品数", ascending=False)
    local_brands["均价"] = local_brands["均价"].apply(lambda x: f"€{x:.2f}" if pd.notna(x) else "N/A")
    st.dataframe(local_brands, use_container_width=True, hide_index=True)
    st.caption("Dampfdorado是最大本土品牌（20个SKU），ZAZO、Herrlan、5EL各有6-9个SKU，均聚焦精品烟油细分市场。")

    # 本土品牌均价 vs 外来品牌（仅烟油对比，公平对比同品类）
    st.markdown('<p class="section-title">💶 同品类价格对比：本土烟油 vs 外来烟油</p>', unsafe_allow_html=True)
    liq_price = fdf[(fdf["产品类型"] == "烟油")].dropna(subset=["价格_数值"])
    liq_price_cmp = liq_price.groupby("是否德国本土品牌")["价格_数值"].describe().reset_index()
    liq_price_cmp["来源"] = liq_price_cmp["是否德国本土品牌"].map({"是": "🇩🇪 德国本土", "否": "🌍 外来品牌"})
    fig_lpc = px.box(liq_price, x="是否德国本土品牌", y="价格_数值",
                     color="是否德国本土品牌",
                     color_discrete_map={"是": COLORS["germany"], "否": COLORS["china"]},
                     points="all", template=T,
                     labels={"是否德国本土品牌": "来源", "价格_数值": "价格（€）"})
    fig_lpc.update_layout(showlegend=False, xaxis_title="来源（否=外来）")
    st.plotly_chart(fig_lpc, use_container_width=True)
    st.caption("德国本土烟油均价€8.31 vs 外来烟油€8.15，价格几乎持平；本土品牌无明显价格溢价，需依靠口味差异化竞争。")

# ========== TAB 9 总结洞察 ==========
with tabs[9]:
    st.markdown("## 📝 市场总结与关键洞察")

    real_top_flavors = fdf["口味名称"].value_counts().head(3).index.tolist()
    real_top_elements = Counter([t for tl in fdf["口味标签列表"] for t in tl]).most_common(3)
    real_top_elements_str = ", ".join([f"{elem} ({cnt})" for elem, cnt in real_top_elements])

    st.markdown('<div class="summary-card">', unsafe_allow_html=True)
    st.markdown(f"### 🧊 1. 冰感（Ice）与莓果是跨品类、跨渠道的核心元素")
    st.markdown(f"- 「ice」是所有口味标签中出现频率**最高的单一元素**，远超第二位blueberry。")
    st.markdown(f"- **最高频双元素组合**为 blueberry + raspberry，其次是 ice + strawberry、blue raspberry + lemonade、kiwi + strawberry、ice + peach、blueberry + ice、kiwi + passion fruit，「莓果」与「冰感」是市场上最强势的口味语言。")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="summary-card">', unsafe_allow_html=True)
    st.markdown(f"### 🍇 2. 水果口味统治市场，复合口味成主流")
    st.markdown(f"- 水果分类占比 **{(fdf['分类']=='水果').sum()/len(fdf)*100:.0f}%**，是第二名饮料的7倍以上。")
    st.markdown(f"- 全市场最热门口味为 **Blueberry Sour Raspberry**（出现8次最多），其次是 **Blue Razz Lemonade、Blueberry、Watermelon**（均为7次并列第二）。")
    comp_ratio = (fdf['口味复杂度'].isin(['双重复合','三重以上复合']).sum() / len(fdf)) * 100
    st.markdown(f"- 复合口味占比 **{comp_ratio:.0f}%**，双重复合是最受欢迎的复杂度（Blueberry Sour Raspberry、Strawberry Kiwi等）。")
    st.markdown(f"- 含烟草口味仅占约3%，且几乎全部集中在德国本土烟油品牌，反映德国市场口味烟草口味占热销榜单比例较小。")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="danger-card">', unsafe_allow_html=True)
    st.markdown("### 🖤 3. 大口数产品构成市场重要变量")
    st.markdown(f"- 大口数一次性占全数据集 **{(fdf['产品类型']=='大口数一次性').sum()/len(fdf)*100:.0f}%**，但覆盖 **8个** 专营渠道。")
    st.markdown("- 三品牌（Fumot、Vozol、AL FAKHER）均价存在差异，AL FAKHER 走品牌溢价路线，均价明显更高。")
    st.markdown("- 大口数产品含冰比例更高，尼古丁策略两极化：AL FAKHER 多用低浓度（6mg）游离尼古丁，Fumot/Vozol  用超高浓度（最高50mg）盐尼古丁。")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="summary-card">', unsafe_allow_html=True)
    st.markdown("### 💊 4. 尼古丁生态高度分化")
    st.markdown("- 合规Pod全部锁定20mg盐尼古丁（TPD上限），**合规市场已完全标准化**。")
    st.markdown("- 烟油产品提供多档浓度选择，0mg无尼古丁产品也有市场，有望成为减量戒烟场景的补充。")
    st.markdown("- 大口数产品出现远超合规范围的超高浓度（如50mg），与烟油/合规Pod形成鲜明分化。")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="summary-card">', unsafe_allow_html=True)
    st.markdown("### 🇩🇪 5. 本土品牌形成差异化生态位")
    st.markdown("- **德国本土品牌7个，100% 集中在瓶装烟油**，完全回避一次性设备赛道。")
    st.markdown("- 本土品牌在烟草、薄荷口味上占比显著高于外来品牌，口味偏好更传统。")
    st.markdown("- 本土 vs 外来烟油均价几乎持平（€8.31 vs €8.15），**本土品牌没有价格溢价**，需通过口味独特性和本土品牌认知差异化。")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="warning-card">', unsafe_allow_html=True)
    st.markdown("### 🌐 6. 渠道结构呈双轨并行格局")
    st.markdown("- **综合零售渠道**（5家）：售卖合规Pod+烟油，热销口味结构趋同，竞争激烈，单价€6-10。")
    st.markdown("- **黑市专营渠道**（8家）：品牌官方站或代理站，专售大口数，单价€11-25，利润空间更大。")
    st.markdown("- 两类渠道**无交叉**，形成互不侵犯的平行市场。")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="summary-card">', unsafe_allow_html=True)
    st.markdown("### 📢 7. 产品开发建议")
    st.markdown("- **必押莓果、水果+冰**：莓果类仍是最稳妥的起点，跨品类通用。")
    st.markdown("- **双重复合口味优先**：单一水果正在失去竞争力，「A+B」组合（如Strawberry Kiwi、Peach Berry）是爆款孵化器。")
    st.markdown("- **烟油提供多档浓度**：0/3/6/9/12/18/20mg多档可满足不同尼古丁需求用户。")
    st.markdown("- **本土差异化路线**：烟草/薄荷/咖啡/甜点口味是外来品牌的盲区，本土品牌可深耕。")
    st.markdown('</div>', unsafe_allow_html=True)

# ========== TAB 10 原始数据 ==========
with tabs[10]:
    st.markdown("### 📋 原始数据浏览")
    show_cols = ["网站名称", "产品类型", "排名", "品牌", "是否德国本土品牌", "口味名称", "口味标签",
                 "分类", "含冰/薄荷", "含烟草", "尼古丁浓度mg", "容量ml", "是否合规", "品牌来源国", "价格"]
    search = st.text_input("🔍 搜索口味名称 / 品牌 / 标签")
    display_df = fdf[show_cols].sort_values(["产品类型", "网站名称", "排名"])
    if search:
        mask = display_df.apply(lambda row: search.lower() in str(row).lower(), axis=1)
        display_df = display_df[mask]
    st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)
    st.caption(f"共 {len(display_df)} 条记录")