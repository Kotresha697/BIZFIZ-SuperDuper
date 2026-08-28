import React, { useState, useEffect, useCallback } from 'react'
import NavBar from '../../component/NavBar'
import RequestList from './RequestList'
import './index.css'
import Loading from '../../component/Loading';
import RequestTable from '../../component/RequestTable';
import adminApi from '../../api';

const AllRequestPage = () => {



    const [allData, setAllData] = useState([]);
    const [allDataSecond, setAllDataSecond] = useState([]);
    const [counts, setCounts] = useState({ total: 0, pending: 0, review: 0, approved: 0, rejected: 0 });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const loadData = useCallback(() => {
        // Admin-protected endpoint; bearer token attached by the shared instance.
        adminApi.get("/api/admin/applications")
            .then((res) => {
                    // Awaiting a decision: Pending (0) and Under Review (2).
                    let first = res.data.filter((item)=>{
                        return item.applicationStatus == 0 || item.applicationStatus == 2
                    })
                    // Decided: Approved (1) and Rejected (3).
                    let second = res.data.filter((item)=>{
                        return item.applicationStatus == 1 || item.applicationStatus == 3
                    })

                    setAllData(first)
                    setAllDataSecond(second)
                    // At-a-glance totals for the admin (section 26), computed from
                    // the same fetched list — no extra API call. Real counts only.
                    const all = res.data || []
                    const by = (s) => all.filter((item) => item.applicationStatus === s).length
                    setCounts({
                        total: all.length,
                        pending: by(0),
                        review: by(2),
                        approved: by(1),
                        rejected: by(3)
                    })
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
    return (
        <>
            <NavBar title={"Bank Admin : All Forms"} showBackIcon={false} />
           <br/>
           <div className="request-list">
           <h5 className="px-3 " style={{textAlign:'center'}}> 📃 All Requested Application </h5>
            <div className="requesPage mx-4 my-3">
                {(loading) ? (
                    <Loading />
                ) : error ? (
                    <div className="alert alert-warning mx-3" role="alert">{error}</div>
                ) : (<>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', margin: '4px 4px 22px' }}>
                        {[
                            { label: 'Total', value: counts.total, color: '#3730a3', bg: '#eef2ff' },
                            { label: 'Pending', value: counts.pending, color: '#1d4ed8', bg: '#dbeafe' },
                            { label: 'Under Review', value: counts.review, color: '#92400e', bg: '#fef3c7' },
                            { label: 'Approved', value: counts.approved, color: '#166534', bg: '#dcfce7' },
                            { label: 'Rejected', value: counts.rejected, color: '#991b1b', bg: '#fee2e2' }
                        ].map((c) => (
                            <div key={c.label} style={{ flex: '1 1 130px', minWidth: '130px', padding: '16px 18px', borderRadius: '12px', background: c.bg, border: '1px solid rgba(15,23,42,.06)' }}>
                                <div style={{ fontSize: '26px', fontWeight: 800, color: c.color, lineHeight: 1 }}>{c.value}</div>
                                <div style={{ marginTop: '6px', fontSize: '11px', fontWeight: 800, letterSpacing: '.06em', textTransform: 'uppercase', color: '#475569' }}>{c.label}</div>
                            </div>
                        ))}
                    </div>

                    <RequestList title={"To Review "} userData={allData} />
                    <RequestList title={"Reviewed"} userData={allDataSecond} />
                    </>
                )}

            </div>
            </div>

        </>
    )
}

export default AllRequestPage
