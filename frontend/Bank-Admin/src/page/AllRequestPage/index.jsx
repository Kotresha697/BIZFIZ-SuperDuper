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
