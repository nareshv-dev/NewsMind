import streamlit as st
import os
import requests
import pandas as pd
import altair as alt
import html
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="NewsMind Viewer",
    page_icon="📰",
    layout="wide"
)

# -------------------------
# PREMIUM INJECTED CSS
# -------------------------
st.markdown("""
<style>
/* Font import */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

/* Apply font to Streamlit app */
.stApp, html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Custom modern header */
.hero-header {
    background: linear-gradient(135deg, #1e1b4b 0%, #311042 50%, #030712 100%);
    padding: 2.5rem 1.5rem;
    border-radius: 20px;
    margin-bottom: 2rem;
    border: 1px solid rgba(255, 255, 255, 0.08);
    text-align: center;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.hero-title {
    background: linear-gradient(90deg, #a5b4fc 0%, #f472b6 50%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    letter-spacing: -1px;
}

.hero-subtitle {
    color: #9ca3af;
    font-size: 1.05rem;
    font-weight: 400;
}

/* Grid Layout for News Cards */
.news-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 1.5rem;
    margin-top: 1.5rem;
    margin-bottom: 2.5rem;
}

/* Card Styling */
.news-card {
    background-color: var(--secondary-background-color);
    border: 1px solid rgba(128, 128, 128, 0.15);
    border-radius: 16px;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    flex-direction: column;
    height: 100%;
    position: relative;
}

.news-card:hover {
    transform: translateY(-6px);
    border-color: var(--primary-color);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}

.card-img-container {
    position: relative;
    width: 100%;
    height: 180px;
    overflow: hidden;
    background: rgba(128, 128, 128, 0.05);
}

.card-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.5s ease;
}

.news-card:hover .card-img {
    transform: scale(1.05);
}

.card-content {
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    flex-grow: 1;
}

.card-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
}

.source-badge {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
    color: var(--primary-color);
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border: 1px solid rgba(99, 102, 241, 0.2);
}

.pub-date {
    color: var(--text-color);
    opacity: 0.6;
    font-size: 0.7rem;
    font-weight: 500;
}

.card-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text-color);
    line-height: 1.4;
    margin-bottom: 0.75rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    height: 3.1rem;
}

.card-desc {
    font-size: 0.85rem;
    color: var(--text-color);
    opacity: 0.75;
    line-height: 1.5;
    margin-bottom: 1.25rem;
    flex-grow: 1;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    height: 3.8rem;
}

.card-link-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
    color: #ffffff !important;
    padding: 0.55rem 1rem;
    border-radius: 10px;
    font-size: 0.8rem;
    font-weight: 600;
    text-decoration: none !important;
    transition: all 0.2s ease;
    box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2);
    text-align: center;
}

.card-link-btn:hover {
    background: linear-gradient(90deg, #4338ca 0%, #6d28d9 100%);
    transform: translateY(-1px);
    box-shadow: 0 8px 12px -2px rgba(79, 70, 229, 0.35);
}

/* Metric card styling */
.metric-container {
    background-color: var(--secondary-background-color);
    border: 1px solid rgba(128, 128, 128, 0.15);
    border-radius: 12px;
    padding: 1.25rem;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}
.metric-val {
    font-size: 1.8rem;
    font-weight: 800;
    color: var(--primary-color);
}
.metric-lbl {
    font-size: 0.8rem;
    color: var(--text-color);
    opacity: 0.6;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# HEADER
# -------------------------
st.markdown("""
<div class="hero-header">
    <div class="hero-title">NewsMind Intelligence Hub</div>
    <div class="hero-subtitle">Discover, analyze, and gain insight into global news powered by advanced search indices</div>
</div>
""", unsafe_allow_html=True)

# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.markdown("""
<div style='text-align: center; padding-bottom: 1rem;'>
    <span style='font-size: 3rem;'>🧠</span>
    <h3 style='margin: 10px 0 0 0;'>NewsMind Settings</h3>
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()

api_key = st.sidebar.text_input(
    "News API Key",
    value=os.environ.get("NEWSAPI_KEY", ""),
    type="password",
    help="Enter your News API key. A working key is prefilled."
)

st.sidebar.markdown("### 🔍 Search Queries")

# Popular topics quick selectors
quick_topics = ["Artificial Intelligence", "Quantum Computing", "Global Economy", "Climate Change", "Space Exploration", "Cybersecurity"]
selected_quick_topic = st.sidebar.selectbox(
    "Quick Topics",
    ["Custom Search..."] + quick_topics
)

if selected_quick_topic == "Custom Search...":
    search_query = st.sidebar.text_input(
        "Search Keyword / Phrase",
        value="Artificial Intelligence"
    )
else:
    search_query = st.sidebar.text_input(
        "Search Keyword / Phrase",
        value=selected_quick_topic
    )

page_size = st.sidebar.slider(
    "Number of Articles to Fetch",
    min_value=5,
    max_value=50,
    value=15,
    step=5
)

# Advanced Sort By Option
sort_by = st.sidebar.selectbox(
    "Sort Articles By",
    options=["publishedAt", "relevance", "popularity"],
    format_func=lambda x: {
        "publishedAt": "Publish Date (Newest)",
        "relevance": "Relevance to Query",
        "popularity": "Popularity / Engagement"
    }[x]
)

# -------------------------
# FETCH NEWS FUNCTION
# -------------------------
@st.cache_data(ttl=600)  # Cache results for 10 minutes to make it extremely responsive and fast!
def fetch_news(query, api_key, limit, sort_method):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": sort_method,
        "pageSize": limit,
        "apiKey": api_key
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "message": f"API returned status code {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# -------------------------
# PDF GENERATION UTILITIES
# -------------------------
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Header (Only on page 2 and later)
        if self._pageNumber > 1:
            self.drawString(54, 750, "NewsMind Intelligence Hub — News Report")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)
            
        # Footer (On all pages)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 40, page_text)
        self.drawString(54, 40, "Confidential — Generated by NewsMind")
        self.restoreState()

def escape_xml(text):
    if not text:
        return ""
    text = html.unescape(text)
    text = (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))
    text = text.replace('\n', '<br/>')
    return text

def generate_summary(articles, for_pdf=False):
    import re
    # Generates a bulleted executive summary of the feed
    summary_points = []
    
    # 1. Source analysis
    sources = [a.get("source", {}).get("name") or "Unknown" for a in articles]
    from collections import Counter
    source_counts = Counter(sources)
    top_sources = [s for s, c in source_counts.most_common(2)]
    
    # 2. Topic/Keyword analysis
    words = []
    stop_words = {'the', 'a', 'and', 'in', 'of', 'to', 'for', 'on', 'with', 'at', 'by', 'an', 'is', 'it', 'from', 'that', 'as', 'are', 'was', 'be', 'this', 'has', 'about', 'new', 'more', 'us', 'after'}
    for a in articles:
        title = a.get("title") or ""
        title_words = re.findall(r'\w+', title.lower())
        words.extend([w for w in title_words if w not in stop_words and len(w) > 3])
    
    word_counts = Counter(words)
    top_keywords = [w.capitalize() for w, c in word_counts.most_common(3)]
    
    def clean(txt):
        if not txt:
            return ""
        txt = re.sub('<[^<]+?>', '', txt)
        txt = html.escape(html.unescape(txt))
        return txt

    # 3. Overall executive summary paragraph
    exec_summary = f"This report synthesizes {len(articles)} recent articles. "
    if top_keywords:
        exec_summary += f"The primary themes revolve around key concepts like <b>{', '.join([clean(k) for k in top_keywords])}</b>. "
    if top_sources:
        exec_summary += f"Key reporting coverage is driven by prominent news outlets including <b>{', '.join([clean(s) for s in top_sources])}</b>."
        
    summary_points.append(exec_summary)
    
    # 4. Generate key takeaways/bullet points for top 8 articles
    summary_points.append("<br/><b>Key Highlights &amp; Takeaways:</b>" if for_pdf else "<br/><b>Key Highlights & Takeaways:</b>")
    for article in articles[:8]:
        title = article.get("title") or "No Title"
        desc = article.get("description") or ""
        sentences = desc.split('. ')
        bullet = sentences[0].strip() if sentences else "No description available."
        if bullet and not bullet.endswith('.'):
            bullet += '.'
        
        escaped_title = clean(title)
        escaped_bullet = clean(bullet)
        
        summary_points.append(f"• <b>{escaped_title}:</b> {escaped_bullet}")
        
    return "<br/>".join(summary_points)

def generate_pdf_report(articles, query):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name='DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1E1B4B'),
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        name='DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=15
    )
    section_heading_style = ParagraphStyle(
        name='SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=colors.HexColor('#4F46E5'),
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    summary_box_style = ParagraphStyle(
        name='SummaryBoxText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#1E293B')
    )
    article_title_style = ParagraphStyle(
        name='ArticleTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#311042'),
        spaceBefore=12,
        spaceAfter=4,
        keepWithNext=True
    )
    meta_style = ParagraphStyle(
        name='ArticleMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#475569'),
        spaceAfter=6,
        keepWithNext=True
    )
    desc_style = ParagraphStyle(
        name='ArticleDesc',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=8
    )
    url_style = ParagraphStyle(
        name='ArticleURL',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#4F46E5'),
        spaceAfter=15
    )

    story = []
    story.append(Spacer(1, 15))
    story.append(Paragraph("NewsMind Intelligence Report & Summary", title_style))
    
    meta_desc = f"<b>Generated on:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    meta_desc += f"<b>Search Query:</b> \"{query}\" | "
    meta_desc += f"<b>Total Articles Analyzed:</b> {len(articles)}"
    story.append(Paragraph(meta_desc, subtitle_style))
    
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#E2E8F0'), spaceAfter=15))
    
    # --- Executive Summary Section ---
    story.append(Paragraph("🧠 AI Executive Summary", section_heading_style))
    
    summary_text = generate_summary(articles, for_pdf=True)
    summary_p = Paragraph(summary_text, summary_box_style)
    summary_table = Table([[summary_p]], colWidths=[504])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))
    
    # --- Feed Details Section ---
    story.append(Paragraph("Detailed Article Feed", section_heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=10))
    
    for idx, article in enumerate(articles, 1):
        title = article.get("title") or "No Title"
        source = (article.get("source") or {}).get("name") or "Unknown Source"
        pub_date = (article.get("publishedAt") or "")[:10]
        desc = article.get("description") or "No description available."
        content = article.get("content") or ""
        url = article.get("url") or "#"
        
        story.append(Paragraph(f"{idx}. {title}", article_title_style))
        meta_info = f"Source: <b>{source}</b> | Published: <b>{pub_date}</b>"
        story.append(Paragraph(meta_info, meta_style))
        
        full_text = desc
        if content and len(content) > len(desc):
            full_text = content
            
        clean_text = escape_xml(full_text)
        story.append(Paragraph(clean_text, desc_style))
        
        escaped_url = escape_xml(url)
        url_link = f'Read Full Article: <font color="#4F46E5"><u><a href="{escaped_url}">{escaped_url}</a></u></font>'
        story.append(Paragraph(url_link, url_style))
        
        if idx < len(articles):
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#F1F5F9'), spaceAfter=10))
            
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()

# -------------------------
# MAIN LOGIC
# -------------------------
# Create main tabs
tab_feed, tab_analytics = st.tabs(["📰 Feed Grid", "📊 Insights & Analytics"])

if not api_key:
    st.warning("Please enter your News API Key in the sidebar.")
    st.stop()

# Fetch the news
with st.spinner("Fetching latest news articles..."):
    data = fetch_news(search_query, api_key, page_size, sort_by)

if data and data.get("status") == "ok":
    articles = data.get("articles", [])
    
    if len(articles) == 0:
        with tab_feed:
            st.info("No articles found matching the search criteria. Try another keyword.")
        with tab_analytics:
            st.info("No data available for analytics.")
    else:
        # Feed tab
        with tab_feed:
            col_title, col_action = st.columns([2, 1])
            with col_title:
                st.markdown(f"### Latest updates for *\"{search_query}\"*")
            with col_action:
                pdf_data = generate_pdf_report(articles, search_query)
                st.download_button(
                    label="📄 Download Summary & Report PDF",
                    data=pdf_data,
                    file_name=f"NewsMind_Summary_Report_{search_query.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            # Show the AI Summary in a beautiful glassmorphic container
            st.markdown("#### 🧠 AI Executive Summary")
            summary_html = generate_summary(articles, for_pdf=False)
            st.markdown(f'<div style="background-color: var(--secondary-background-color); border: 1px solid rgba(128, 128, 128, 0.15); border-radius: 16px; padding: 1.5rem; margin-bottom: 2rem;">{summary_html}</div>', unsafe_allow_html=True)
            
            grid_items = []
            for i, article in enumerate(articles, start=1):
                img_url = article.get("urlToImage")
                if img_url:
                    img_html = f'<div class="card-img-container"><img src="{img_url}" class="card-img" alt="News Image"></div>'
                else:
                    img_html = '<div class="card-img-container" style="display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%);"><span style="font-size: 3rem;">📰</span></div>'
                
                title = article.get("title") or "No Title"
                title_escaped = title.replace('"', '&quot;')
                source_name = (article.get("source") or {}).get("name") or "Unknown Source"
                published_date = (article.get("publishedAt") or "")[:10]
                description = article.get("description") or "No description available."
                url = article.get("url") or "#"
                
                card_html = f'<div class="news-card">{img_html}<div class="card-content"><div class="card-meta"><span class="source-badge">{source_name}</span><span class="pub-date">{published_date}</span></div><h3 class="card-title">{title_escaped}</h3><p class="card-desc">{description}</p><a class="card-link-btn" href="{url}" target="_blank">Read Full Article</a></div></div>'
                grid_items.append(card_html)
                
            grid_html = f'<div class="news-grid">{"".join(grid_items)}</div>'
            st.markdown(grid_html, unsafe_allow_html=True)

        # Analytics Tab
        with tab_analytics:
            st.markdown("### 📊 Search Feed Analytics")
            
            # Convert articles to DataFrame for charting
            df_articles = pd.DataFrame([
                {
                    "Source": (a.get("source") or {}).get("name") or "Unknown",
                    "Date": (a.get("publishedAt") or "")[:10],
                    "Title": a.get("title", ""),
                } for a in articles
            ])
            
            # Metrics
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-val">{len(articles)}</div>
                    <div class="metric-lbl">Total Articles</div>
                </div>
                """, unsafe_allow_html=True)
            with col_m2:
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-val">{df_articles["Source"].nunique()}</div>
                    <div class="metric-lbl">Unique Sources</div>
                </div>
                """, unsafe_allow_html=True)
            with col_m3:
                # Most active source
                active_source = df_articles["Source"].mode().values[0] if not df_articles.empty else "N/A"
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-val" style="font-size: 1.3rem; line-height: 2.1rem;">{active_source}</div>
                    <div class="metric-lbl">Top Publisher</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.write("")
            st.divider()
            
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("#### Articles by News Source")
                source_counts = df_articles["Source"].value_counts().reset_index()
                source_counts.columns = ["Source", "Articles Count"]
                
                # Altair Chart
                chart_sources = alt.Chart(source_counts).mark_bar(
                    cornerRadiusTopLeft=8,
                    cornerRadiusTopRight=8
                ).encode(
                    x=alt.X("Source:N", sort="-y", title="News Outlet"),
                    y=alt.Y("Articles Count:Q", title="Volume"),
                    color=alt.Color("Source:N", legend=None, scale=alt.Scale(scheme="purples")),
                    tooltip=["Source", "Articles Count"]
                ).properties(height=350)
                st.altair_chart(chart_sources, use_container_width=True)
                
            with col_chart2:
                st.markdown("#### Timeline of Publications")
                date_counts = df_articles["Date"].value_counts().reset_index()
                date_counts.columns = ["Date", "Articles Count"]
                date_counts = date_counts.sort_values("Date")
                
                chart_dates = alt.Chart(date_counts).mark_area(
                    line={"color": "#6366f1"},
                    color=alt.Gradient(
                        gradient="linear",
                        stops=[
                            alt.GradientStop(color="#818cf8", offset=0),
                            alt.GradientStop(color="rgba(129, 140, 248, 0.1)", offset=1)
                        ],
                        x1=1, y1=1, x2=1, y2=0
                    )
                ).encode(
                    x=alt.X("Date:T", title="Publication Date"),
                    y=alt.Y("Articles Count:Q", title="Volume"),
                    tooltip=["Date", "Articles Count"]
                ).properties(height=350)
                st.altair_chart(chart_dates, use_container_width=True)

else:
    error_msg = data.get("message") if data else "Unknown error occurred"
    st.error(f"Failed to fetch news. {error_msg}")
    st.info("💡 Make sure your API key is correct and you have an active internet connection.")


