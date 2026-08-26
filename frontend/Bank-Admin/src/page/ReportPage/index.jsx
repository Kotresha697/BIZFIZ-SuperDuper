import React, { useState, useEffect, useCallback } from 'react'
import Loading from '../../component/Loading';
import  NavBar from '../../component/NavBar'
import FullReport from './FullReport';
import adminApi from '../../api';

const ReportPage = ({match}) => {
    const [reportData, setReportData] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    //const fetchData = async
    const loadData = useCallback(() => {
        // Canonical admin analysis endpoint: returns the REAL stored application
        // plus its BizFiz analysis, keyed by the MongoDB application id.
        adminApi.get(`/api/admin/analysis/${match.params.reportId}`)
            .then((res) => {
                setReportData(res.data)
                setError("")
                setLoading(false);
            }).catch((err) => {
                const detail = err && err.response && err.response.data ? err.response.data.detail : null;
                // Always leave the loading state so the page cannot spin forever.
                setError(typeof detail === 'string' ? detail : "Unable to fetch this application. Please refresh.")
                setLoading(false);
            })
    }, [match.params.reportId]);

    useEffect(() => {
        loadData()
    }, [loadData])
    return (
        <>
         <NavBar title={`Bank Admin : Form Details of ${match.params.reportId}`} showBackIcon={true}/>
         <div className="request-list">
         {(loading) ? (
                    <Loading />
                ) : error ? (
                    <div className="alert alert-warning mx-3" style={{margin:'30px 10px'}} role="alert">{error}</div>
                ) : (<>

                   <h5 className="px-3 " style={{textAlign:'center', margin:'30px 10px'}}> 📃 Form ID : {match.params.reportId} </h5>


           <FullReport reportData={reportData} reportId={match.params.reportId}/>
                    </>
                )}

          </div>
        </>
    )
}

export default ReportPage
