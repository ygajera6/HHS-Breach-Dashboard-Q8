"""
Research question 8 | Hacking vs. Unauthorized Disclosure
HHS OCR healthcare breach dashboard (adapted from the class starter template)

Research question: How do hacking/IT incidents and unauthorized access or
disclosure differ in their reported patterns and consequences?

Interactive features: (1) dropdown filters, (2) date range slider
Visualizations:       (1) bar chart, (2) pie chart, (3) line chart
"""
from datetime import date
from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='Hacking vs. Unauthorized Disclosure', layout='wide')
st.title('Hacking vs. Unauthorized Disclosure in Healthcare Breaches')
st.caption('Research question 8 | Cyber Risk Management | Public HHS OCR breach reports (current + archive, snapshot November 10, 2026)')

FILENAME = 'hhs_breaches.xlsx'          # Change only if the workbook has a different name.
STUDY_START = date(2020, 1, 1)          # Project scope: submissions from January 1, 2020 onward.

HACK = 'Hacking/IT Incident'
UAD = 'Unauthorized Access/Disclosure'
COLORS = {HACK: '#2a6fdb', UAD: '#e8833a'}
GROUP_ORDER = [HACK, UAD]


# ---------------------------------------------------------------- load data
@st.cache_data
def load_excel(content):
    return pd.read_excel(BytesIO(content))  # BytesIO: newer pandas no longer accepts raw bytes


uploaded = st.sidebar.file_uploader('Optional: upload an Excel workbook', type='xlsx')
if uploaded:
    content = uploaded.getvalue()
elif (Path(__file__).parent / FILENAME).exists():
    content = (Path(__file__).parent / FILENAME).read_bytes()
else:
    st.info(f'Add {FILENAME} to the same GitHub repository as app.py, or upload it in the sidebar.')
    st.stop()
try:
    df = load_excel(content)
except Exception as e:
    st.error(f'Unable to read Excel: {e}')
    st.stop()
df.columns = [str(c).strip() for c in df.columns]
if df.empty or df.columns.duplicated().any():
    st.error('Workbook is empty or has duplicate column names. Check the Excel file.')
    st.stop()


def find_col(*names):
    normalized = {''.join(c.lower().split()).replace('_', ''): c for c in df.columns}
    for name in names:
        key = ''.join(name.lower().split()).replace('_', '')
        if key in normalized:
            return normalized[key]
    return None


date_col = find_col('Breach Submission Date', 'Submission Date')
state_col = find_col('State')
type_col = find_col('Type of Breach', 'Breach Type')
count_col = find_col('Individuals Affected', 'Number of Individuals Affected')
entity_col = find_col('Covered Entity Type', 'Entity Type')
associate_col = find_col('Business Associate Present', 'Business Associate Involved')
location_col = find_col('Location of Breached Information', 'Location of Breach')

missing = [n for n, c in [('Breach Submission Date', date_col), ('Type of Breach', type_col),
                          ('Individuals Affected', count_col), ('Location of Breached Information', location_col)] if not c]
if missing:
    st.error('This dashboard needs these HHS columns: ' + ', '.join(missing))
    st.stop()

# ---------------------------------------------------------- transformations
work = df.copy()
work['_date'] = pd.to_datetime(work[date_col], errors='coerce')
work['_year'] = work['_date'].dt.year
work['_affected'] = pd.to_numeric(work[count_col].astype(str).str.replace(',', '', regex=False), errors='coerce')

# A report can list several breach types (e.g. "Theft, Unauthorized Access/Disclosure").
# Comparison group: reports listing hacking but not UAD, reports listing UAD but not hacking.
# Reports listing BOTH are excluded so no report is counted on both sides.
types = work[type_col].fillna('').astype(str)
has_hack = types.str.contains(HACK, regex=False)
has_uad = types.str.contains(UAD, regex=False)
work['_group'] = None
work.loc[has_hack & ~has_uad, '_group'] = HACK
work.loc[has_uad & ~has_hack, '_group'] = UAD

in_scope = work['_date'].dt.date >= STUDY_START
excluded = {
    'Submitted before 2020-01-01': int((~in_scope).sum()),
    'Other breach types (theft, loss, disposal, other, unknown)': int((in_scope & ~has_hack & ~has_uad).sum()),
    'Lists both hacking and UAD': int((in_scope & has_hack & has_uad).sum()),
}
work = work[in_scope & work['_group'].notna()].copy()

# A report can also list several locations ("Email, Network Server").
# For location charts, split into one row per location listed.
loc_long = work.assign(_location=work[location_col].fillna('Not reported').astype(str).str.split(','))
loc_long = loc_long.explode('_location')
loc_long['_location'] = loc_long['_location'].str.strip()

# ---------------------------------------------------- interactive features
st.sidebar.header('Interactive filters')

# Feature 1: Date range slider
min_d, max_d = work['_date'].min().date(), work['_date'].max().date()
start_d, end_d = st.sidebar.slider('Breach submission date range', min_value=min_d, max_value=max_d,
                                   value=(min_d, max_d), format='MMM YYYY')

# Feature 2: Dropdown filters
compare = st.sidebar.selectbox('Breach types to show', ['Side by side (both)', HACK, UAD])


def dropdown(label, column):
    if not column:
        return 'All'
    options = ['All'] + sorted(work[column].dropna().astype(str).unique().tolist())
    return st.sidebar.selectbox(label, options)


entity_choice = dropdown('Covered entity type', entity_col)
state_choice = dropdown('State', state_col)
associate_choice = dropdown('Business associate present', associate_col)
location_options = ['All'] + sorted(loc_long['_location'].unique().tolist())
location_choice = st.sidebar.selectbox('Information location', location_options)


def apply_filters(frame, location_field):
    m = frame['_date'].dt.date.between(start_d, end_d)
    if compare != 'Side by side (both)':
        m &= frame['_group'] == compare
    for column, choice in [(entity_col, entity_choice), (state_col, state_choice), (associate_col, associate_choice)]:
        if column and choice != 'All':
            m &= frame[column].astype(str) == choice
    if location_choice != 'All':
        if location_field == '_location':
            m &= frame['_location'] == location_choice
        else:
            m &= frame[location_col].fillna('').astype(str).str.split(',').apply(
                lambda xs: location_choice in [x.strip() for x in xs])
    return frame[m]


view = apply_filters(work, location_col)
view_loc = apply_filters(loc_long, '_location')
groups = [g for g in GROUP_ORDER if g in view['_group'].unique()]

with st.sidebar.expander('Data preparation notes'):
    st.write(f'Workbook records: {len(df):,}')
    for k, v in excluded.items():
        st.write(f'Excluded, {k.lower()}: {v:,}')
    st.write(f'Records in comparison: {len(work):,}')

# ------------------------------------------------------------------ summary
st.subheader('Side-by-side summary')
if view.empty:
    st.warning('No records match the selected filters. Change the filters to continue.')
    st.stop()

def short(n):
    for div, suffix in [(1e9, 'B'), (1e6, 'M'), (1e3, 'K')]:
        if n >= div:
            return f'{n / div:,.1f}{suffix}'
    return f'{n:,.0f}'


cols = st.columns(len(groups))
for col, g in zip(cols, groups):
    sub = view[view['_group'] == g]
    with col:
        st.markdown(f"**<span style='color:{COLORS[g]}'>{g}</span>**", unsafe_allow_html=True)
        a, b, c = st.columns(3)
        a.metric('Breach reports', f'{len(sub):,}')
        b.metric('Individuals affected', short(sub['_affected'].sum()), help=f"{sub['_affected'].sum():,.0f} (sum across reports)")
        c.metric('Median per report', f"{sub['_affected'].median():,.0f}" if sub['_affected'].notna().any() else 'n/a')
st.caption('Individuals affected is a sum across reports, not a count of unique people. '
           'Report counts describe reported breaches; they do not measure breach probability or causes.')

# ------------------------------------------------- visualization 1: bar chart
st.subheader('Visualization 1: Where the breached information was located')
bar_measure = st.radio('Measure', ['Share of each type\'s reports (%)', 'Number of reports', 'Individuals affected'],
                       horizontal=True)
loc = view_loc.groupby(['_group', '_location']).agg(Reports=('_group', 'size'),
                                                    Affected=('_affected', 'sum')).reset_index()
loc['Share'] = 100 * loc['Reports'] / loc['_group'].map(view.groupby('_group').size())
y_field = {'Share of each type\'s reports (%)': 'Share', 'Number of reports': 'Reports',
           'Individuals affected': 'Affected'}[bar_measure]
order = loc.groupby('_location')[y_field].sum().sort_values(ascending=False).index.tolist()
fig_bar = px.bar(loc, x='_location', y=y_field, color='_group', barmode='group',
                 color_discrete_map=COLORS, category_orders={'_location': order, '_group': GROUP_ORDER},
                 labels={'_location': 'Location of breached information', '_group': 'Breach type',
                         'Share': '% of reports', 'Affected': 'Individuals affected'},
                 title=f'{bar_measure} by information location')
st.plotly_chart(fig_bar, width='stretch')
st.caption('A report that lists several locations counts once in each location, so shares can add up to more than 100%.')

# ------------------------------------------------- visualization 2: pie chart
st.subheader('Visualization 2: Share of reports vs. share of individuals affected')
totals = view.groupby('_group').agg(Reports=('_group', 'size'), Affected=('_affected', 'sum')).reindex(groups).reset_index()
p1, p2 = st.columns(2)
for column, field, title in [(p1, 'Reports', 'Share of breach reports'),
                             (p2, 'Affected', 'Share of individuals affected')]:
    fig = px.pie(totals, names='_group', values=field, color='_group', color_discrete_map=COLORS,
                 hole=0.35, title=title, labels={'_group': 'Breach type', 'Affected': 'Individuals affected'})
    fig.update_traces(textinfo='percent', sort=False)
    fig.update_layout(legend=dict(orientation='h', y=-0.1))
    column.plotly_chart(fig, width='stretch')
if len(groups) < 2:
    st.caption('Select "Side by side (both)" to compare the two breach types in the pie charts.')

# ------------------------------------------------ visualization 3: line chart
st.subheader('Visualization 3: Trend by submission year')
line_measure = st.radio('Measure ', ['Number of reports', 'Individuals affected', 'Median individuals per report'],
                        horizontal=True)
agg = {'Number of reports': ('_group', 'size'), 'Individuals affected': ('_affected', 'sum'),
       'Median individuals per report': ('_affected', 'median')}[line_measure]
trend = view.groupby(['_year', '_group']).agg(Value=agg).reset_index()
fig_line = px.line(trend, x='_year', y='Value', color='_group', markers=True, color_discrete_map=COLORS,
                   category_orders={'_group': GROUP_ORDER},
                   labels={'_year': 'Submission year', 'Value': line_measure, '_group': 'Breach type'},
                   title=f'{line_measure} by submission year')
fig_line.update_xaxes(dtick=1)
st.plotly_chart(fig_line, width='stretch')
if end_d.year == max_d.year:
    st.caption(f'{max_d.year} is a partial year (data through {max_d:%B %d, %Y}).')

# ------------------------------------------------------------- record table
with st.expander('Explore the filtered records'):
    out = view.drop(columns=['_date', '_year', '_affected']).rename(columns={'_group': 'Comparison group'})
    st.dataframe(out, width='stretch')
    st.download_button('Download filtered data (CSV)', out.to_csv(index=False).encode('utf-8'),
                       file_name='filtered_hacking_vs_uad.csv', mime='text/csv')

st.info('These are reported large breaches (500+ individuals) submitted to HHS OCR. The dashboard shows '
        'differences in reported patterns; it does not establish causes or the probability of a breach at any organization.')
