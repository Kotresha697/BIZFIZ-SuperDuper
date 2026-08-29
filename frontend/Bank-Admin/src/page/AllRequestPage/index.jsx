import React, { useState, useEffect, useCallback, useMemo } from 'react'
import NavBar from '../../component/NavBar'
import './index.css'
import Loading from '../../component/Loading';
import adminApi from '../../api';
import { BarChart, Bar, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const statusLabels = { 0: 'Pending', 1: 'Approved', 2: 'Under Review', 3: 'Rejected' };
const riskColors = { High: '#dc2626', Medium: '#d97706', Low: '#15803d', 'N/A': '#94a3b8' };
const money = (value) => value === null || value === undefined || value === '' ? 'N/A' : `₹${Number(value).toLocaleString('en-IN')}`;
const dateText = (value) => value && !Number.isNaN(new Date(value).getTime()) ? new Date(value).toLocaleDateString() : 'N/A';
const text = (value) => value === null || value === undefined || value === '' ? 'N/A' : String(value);
const riskText = (item) => text(item.riskCategory);
const selectOptions = (items, field) => [...new Set(items.map((item) => item[field]).filter(Boolean))].sort();

function Metric({ label, value }) { return <div className="admin-metric"><strong>{value}</strong><span>{label}</span></div>; }
function Distribution({ title, data, colors }) {
    return <div className="admin-chart"><h3>{title}</h3><ResponsiveContainer width="100%" height={210} debounce={100}><PieChart><Pie data={data} dataKey="value" nameKey="name" innerRadius={48} outerRadius={76} paddingAngle={3}>{data.map((entry, index) => <Cell key={entry.name} fill={(colors && colors[index]) || '#3fb1b5'} />)}</Pie><Tooltip /><Legend /></PieChart></ResponsiveContainer></div>;
}
function AmountOverview({ applications }) {
    const data = applications.slice(0, 12).map((item, index) => ({ name: text(item.businessName) === 'N/A' ? `#${index + 1}` : text(item.businessName).slice(0, 12), Requested: Number(item.amountApplied) || 0, Approved: Number(item.amountApproved) || 0 }));
    return <div className="admin-chart admin-chart-wide"><h3>Requested vs Approved Amount</h3><ResponsiveContainer width="100%" height={210} debounce={100}><BarChart data={data}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis /><Tooltip /><Legend /><Bar dataKey="Requested" fill="#2563eb" /><Bar dataKey="Approved" fill="#16a34a" /></BarChart></ResponsiveContainer></div>;
}

const AllRequestPage = () => {



    const [applications, setApplications] = useState([]);
    const [query, setQuery] = useState('');
    const [filters, setFilters] = useState({ status: '', risk: '', sector: '', state: '', district: '' });
    const [sort, setSort] = useState('date-desc');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const loadData = useCallback(() => {
        // Admin-protected endpoint; bearer token attached by the shared instance.
        adminApi.get("/api/admin/applications")
            .then((res) => {
                    setApplications(res.data || [])
                    setError("")
                setLoading(false);
            }).catch((err)=>{
                // Always leave the loading state, otherwise the page spins forever.
                setError("Unable to fetch applications. Please refresh.")
                setLoading(false);
            })
    }, []);

    useEffect(() => {
        loadData()
    }, [loadData])
    const summary = useMemo(() => {
        const numberAverage = (field) => { const values = applications.map((item) => Number(item[field])).filter((value) => Number.isFinite(value) && value > 0); return values.length ? Math.round(values.reduce((a, b) => a + b, 0) / values.length) : 'N/A'; };
        return { total: applications.length, pending: applications.filter((a) => a.applicationStatus === 0).length, review: applications.filter((a) => a.applicationStatus === 2).length, approved: applications.filter((a) => a.applicationStatus === 1).length, rejected: applications.filter((a) => a.applicationStatus === 3).length, score: numberAverage('bizfizScore'), requested: numberAverage('amountApplied'), approvedAmount: numberAverage('amountApproved'), highRisk: applications.filter((a) => String(a.riskCategory).toLowerCase() === 'high').length };
    }, [applications]);
    const filtered = useMemo(() => {
        const q = query.trim().toLowerCase();
        const result = applications.filter((item) => {
            const matchesQuery = !q || [item.name, item.businessName, item.userId, item.mobileNumber].some((value) => String(value || '').toLowerCase().includes(q));
            return matchesQuery && (!filters.status || String(item.applicationStatus) === filters.status) && (!filters.risk || riskText(item) === filters.risk) && (!filters.sector || (item.businessSector || item.typeOfBusiness) === filters.sector) && (!filters.state || item.businessState === filters.state) && (!filters.district || item.businessDistrict === filters.district);
        });
        const [field, direction] = sort.split('-');
        return result.sort((a, b) => { const av = field === 'date' ? new Date(a.applicationDate).getTime() : field === 'name' ? String(a.name || '').toLowerCase() : Number(a[field === 'score' ? 'bizfizScore' : field === 'requested' ? 'amountApplied' : 'amountApproved']) || 0; const bv = field === 'date' ? new Date(b.applicationDate).getTime() : field === 'name' ? String(b.name || '').toLowerCase() : Number(b[field === 'score' ? 'bizfizScore' : field === 'requested' ? 'amountApplied' : 'amountApproved']) || 0; return (av > bv ? 1 : av < bv ? -1 : 0) * (direction === 'asc' ? 1 : -1); });
    }, [applications, query, filters, sort]);
    const distribution = (field, fallback = 'N/A') => Object.entries(applications.reduce((acc, item) => { const key = text(item[field] || fallback); acc[key] = (acc[key] || 0) + 1; return acc; }, {})).map(([name, value]) => ({ name, value }));
    const statusData = Object.entries(statusLabels).map(([key, name]) => ({ name, value: applications.filter((item) => item.applicationStatus === Number(key)).length })).filter((item) => item.value);
    const sectorData = distribution('businessSector');
    const riskData = distribution('riskCategory');
    return (
        <>
            <NavBar title={"Bank Admin : All Forms"} showBackIcon={false} />
           <br/>
           <div className="request-list">
           <div className="admin-heading"><div><p>AI-Powered Loan Risk Intelligence</p><h1>Application Review Queue</h1><span>Review and manage MSME loan applications using BizFiz intelligence.</span></div></div>
            <div className="requesPage mx-4 my-3 admin-dashboard">
                {(loading) ? (
                    <Loading />
                ) : error ? (
                    <div className="alert alert-warning mx-3" role="alert">{error}</div>
                ) : (<>

                    <section><h2>Portfolio Overview</h2><div className="admin-metrics">{[['Total Applications', summary.total], ['Pending', summary.pending], ['Under Review', summary.review], ['Approved', summary.approved], ['Rejected', summary.rejected], ['Average BizFiz Score', summary.score], ['Average Requested', money(summary.requested)], ['Average Approved', money(summary.approvedAmount)], ['High-Risk Applications', summary.highRisk]].map(([label, value]) => <Metric key={label} label={label} value={value} />)}</div></section>
                    <section id="analytics"><h2>Risk Intelligence <small>Regional &amp; Sector Insights</small></h2><div className="admin-charts"><Distribution title="Application Status" data={statusData} colors={['#2563eb', '#16a34a', '#d97706', '#dc2626']} /><Distribution title="Risk Distribution" data={riskData} colors={riskData.map((item) => riskColors[item.name] || '#94a3b8')} /><Distribution title="Sector Distribution" data={sectorData} /><AmountOverview applications={applications} /></div></section>
                    <section id="applications"><h2>Applications <small>{filtered.length} of {applications.length}</small></h2><div className="admin-filters"><input aria-label="Search applications" placeholder="Search applicant, business, ID, mobile" value={query} onChange={(event) => setQuery(event.target.value)} />{[['status', 'Status', Object.entries(statusLabels).map(([value, label]) => [value, label])], ['risk', 'Risk', [...new Set(applications.map(riskText))].map((value) => [value, value])], ['sector', 'Sector', selectOptions(applications, 'businessSector').map((value) => [value, value])], ['state', 'State', selectOptions(applications, 'businessState').map((value) => [value, value])], ['district', 'District', selectOptions(applications, 'businessDistrict').map((value) => [value, value])]].map(([key, label, options]) => <select key={key} aria-label={label} value={filters[key]} onChange={(event) => setFilters({ ...filters, [key]: event.target.value })}><option value="">{label}</option>{options.map(([value, optionLabel]) => <option key={value} value={value}>{optionLabel}</option>)}</select>)}<select aria-label="Sort applications" value={sort} onChange={(event) => setSort(event.target.value)}><option value="date-desc">Newest</option><option value="date-asc">Oldest</option><option value="requested-desc">Highest Loan Amount</option><option value="requested-asc">Lowest Loan Amount</option><option value="approved-desc">Highest Approved Amount</option><option value="approved-asc">Lowest Approved Amount</option><option value="score-desc">Highest Score</option><option value="score-asc">Lowest Score</option><option value="name-asc">Applicant A-Z</option><option value="name-desc">Applicant Z-A</option></select></div><div className="applications-table-wrap"><table className="applications-table"><thead><tr>{['Application ID', 'Applicant', 'Business', 'Sector', 'Location', 'Requested', 'BizFiz Score', 'Risk', 'Status', 'Date', 'Action'].map((heading) => <th key={heading}>{heading}</th>)}</tr></thead><tbody>{filtered.map((item) => <tr key={item.userId}><td data-label="Application ID">{text(item.userId)}</td><td data-label="Applicant">{text(item.name)}<small>{text(item.mobileNumber)}</small></td><td data-label="Business">{text(item.businessName)}</td><td data-label="Sector">{text(item.businessSector || item.typeOfBusiness)}</td><td data-label="Location">{text(item.businessDistrict)}, {text(item.businessState)}</td><td data-label="Requested">{money(item.amountApplied)}</td><td data-label="BizFiz Score">{text(item.bizfizScore)}</td><td data-label="Risk">{riskText(item)}</td><td data-label="Status"><span className={`status-pill status-${item.applicationStatus}`}>{statusLabels[item.applicationStatus] || 'N/A'}</span></td><td data-label="Date">{dateText(item.applicationDate)}</td><td data-label="Action"><a className="review-link" href={`/report/${item.userId}`}>Review</a></td></tr>)}</tbody></table>{!filtered.length && <div className="empty-state">No applications match these filters.</div>}</div></section>
                    </>
                )}

            </div>
            </div>

        </>
    )
}

export default AllRequestPage
