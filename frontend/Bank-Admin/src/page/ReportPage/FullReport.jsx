import * as React from 'react';
import { styled } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Grid from '@mui/material/Grid';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemAvatar from '@mui/material/ListItemAvatar';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import Avatar from '@mui/material/Avatar';
import ImageIcon from '@mui/icons-material/Image';
import WorkIcon from '@mui/icons-material/Work';
import BeachAccessIcon from '@mui/icons-material/BeachAccess';
import { PieChart, Pie, Legend, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import Progressbar from '../../component/Progressbar';
import SectorCard from './SectorCard';
import { Chip, Typography } from '@mui/material';
import { InsertEmoticonSharp } from '@mui/icons-material';
import Modal from '@mui/material/Modal';
import TextField from '@mui/material/TextField';
import Pdf from "react-to-pdf";
import adminApi from '../../api';
const style = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: 400,
    bgcolor: 'background.paper',
    border: '2px solid #000',
    boxShadow: 24,
    p: 4,
};
const ref = React.createRef();
const options = {
    orientation: 'landscape',
    unit: 'in',
    format: [14, 14]
};
const data01 = [
    { name: 'Group A', value: 400 },
    { name: 'Group B', value: 300 },
    { name: 'Group C', value: 300 },

];

const objctToArray = (obj) => {
    const x = Object.entries(obj);
    return x;

}

const getString = (x) => {
    return x.toString();
}

const getFirstLetter = (x) => {
    return x.charAt(0)
}
const getArrayListSector = (data) => {
    return Object.keys(data || {}).map(key => (` ${key} : ${data[key]} `));
}

// Values that a stored application may legitimately not carry.
const naValue = (value) => {
    return (value === null || value === undefined || value === '') ? 'N/A' : value;
}

const naMoney = (value) => {
    if (value === null || value === undefined || value === '') return 'N/A';
    const n = Number(value);
    if (isNaN(n)) return 'N/A';
    return '₹ ' + n.toLocaleString('en-IN');
}

const getIndicatorList = (list) => {
    // The five regional/sector indicators come from the scoring engine. If
    // scoring produced none, render nothing instead of crashing.
    if (!list || list.length < 5) {
        return [];
    }
    let obj = [
        {
            name: list[0].name,
            rating: list[0].rating,
            listTitle: "competitors",
            list: list[0].competitors,
            remark: list[0].remarks
        },

        {
            name: list[2].name,
            rating: list[2].rating,
            listTitle: "Sectors",
            list: getArrayListSector(list[2].sectors),
            remark: list[2].remark
        },
        {
            name: list[3].name,
            rating: list[3].rating,
            listTitle: "More Prosperous Areas",
            list: list[3].moreProsperousAreas,
            remark: list[3].remark
        },
        {
            name: list[4].name,
            rating: list[4].rating,
            listTitle: "Better Areas",
            list: list[4].betterAreas,
            remark: list[4].remark
        },
        {
            name: list[1].name,
            rating: list[1].rating,
            listTitle: "",
            list: [],
            remark: ""
        },


    ]
    console.log("scrd", obj)
    return obj
}

const Item = styled(Paper)(({ theme }) => ({
    backgroundColor: theme.palette.mode === 'dark' ? '#1A2027' : '#fff',
    ...theme.typography.body2,
    padding: theme.spacing(1),
    color: theme.palette.text.secondary,
}));




const SideBox = (data) => {
    const info = data.data || {};
    const applicant = info['Name'] ? String(info['Name']) : '?';
    return (
        <div className="sidebar">
            <Grid
                container
                spacing={0}
                direction="column"
                alignItems="center"
                justifyContent="center"

            >
                <Avatar sx={{ width: 116, height: 116 }}>{getFirstLetter(applicant)}</Avatar>

            </Grid>
            <Box mt={4}>
                <List >
                    {
                        objctToArray(info).map((item, index) => {
                            return (
                                <ListItem disablePadding key={index}><ListItemButton>

                                    <ListItemText primary={`⚡ ${item[0]} : ${item[1]}`} />
                                </ListItemButton>
                                </ListItem>
                            )
                        })
                    }

                </List>
            </Box>
        </div>

    )
}

const MainBox = ({ piedata, score, scoreScale, credit, risk, recommendation, requested }) => {
    const chartData = piedata || [];
    const scaleText = scoreScale ? ` / ${scoreScale}` : '';
    const scoreText = (score === null || score === undefined || score === '')
        ? 'Score : N/A'
        : `Score : ${score}${scaleText}`;
    return (
        <div className="mainbox">
            <Box sx={{ flexGrow: 1 }}>
                <Grid container >
                    <Grid item xs={6} style={{ borderRight: '0.1px solid grey', minHeight: '40vh' }}>
                        <h5>Score Breakdown : </h5>
                        {chartData.map((item, index) => {
                            return <Chip key={index} size="small" label={`${item.name} : ${item.value} `} style={{ marginRight: '10px' }} />
                        })}

                        <>

                            <PieChart width={300} height={250}>
                                <Pie
                                    dataKey="value"
                                    isAnimationActive={false}
                                    data={chartData}
                                    // startAngle={180}
                                    // endAngle={0}
                                    cx="60%"
                                    cy="50%"
                                    // outerRadius={80}
                                    fill="#8884d8"
                                    label
                                />{
                                    chartData.map((entry, index) => <Cell key={`cell-${index}`} strokeWidth={index === 2 ? 4 : 1} />)
                                }

                                <Tooltip />

                            </PieChart>

                        </>
                    </Grid>
                    <Grid item xs={6}>
                        <Grid container>
                            <Grid item sm={12}>
                                <Box display="flex" justifyContent="flex-end">
                                    <Pdf targetRef={ref} options={options} filename="bizfiz-report.pdf">
                                        {({ toPdf }) => <Button variant="contained" className="btn btn-primary" size="small" onClick={toPdf}>Generate Pdf</Button>}
                                    </Pdf>

                                </Box>
                            </Grid>
                        </Grid>
                        <Box mt={3} ml={3} pt={3}>
                            <List >
                                <ListItem disablePadding><ListItemButton> <ListItemIcon>
                                    < WorkIcon />
                                </ListItemIcon>
                                    <ListItemText primary={
                                        <Typography type="body2" style={{ color: 'black' }}>{`BizFiz ${scoreText}`}</Typography>
                                        } />
                                </ListItemButton>
                                </ListItem>

                                <ListItem disablePadding><ListItemButton> <ListItemIcon>
                                    < WorkIcon />
                                </ListItemIcon>
                                    <ListItemText primary={
                                        <Typography type="body2" style={{ color: 'black' }}>{`Risk Level : ${naValue(risk)}`}</Typography>
                                        } />
                                </ListItemButton>
                                </ListItem>

                                <ListItem disablePadding><ListItemButton> <ListItemIcon>
                                    < WorkIcon />
                                </ListItemIcon>
                                    <ListItemText primary={
                                        <Typography type="body2" style={{ color: 'black' }}>{`Recommendation : ${naValue(recommendation)}`}</Typography>
                                        } />
                                </ListItemButton>
                                </ListItem>

                                <ListItem disablePadding><ListItemButton> <ListItemIcon>
                                    < WorkIcon />
                                </ListItemIcon>
                                    <ListItemText primary={
                                        <Typography type="body2" style={{ color: 'black' }}>{`Requested Amount : ${naMoney(requested)}`}</Typography>
                                        } />
                                </ListItemButton>
                                </ListItem>

                                <ListItem disablePadding><ListItemButton> <ListItemIcon>
                                    < WorkIcon />
                                </ListItemIcon>
                                    <ListItemText primary={
                                          <Typography type="body2" style={{ color: 'black' }}>{`Max Allowed Credit : ${naMoney(credit)}`}</Typography>
                                        } />


                                </ListItemButton>
                                </ListItem>
                            </List>
                        </Box>
                    </Grid>

                </Grid>
            </Box>
        </div>
    )
}

const MainBoxSecond = ({ account, indicators }) => {
    const accountRows = objctToArray(account || {});
    const indicatorRows = indicators || [];
    return (
        <div className="mainbox">
            <Box sx={{ flexGrow: 1 }}  >
                <Grid container spacing={3}>
                    <Grid item xs={6} mt={1} style={{ minHeight: '40vh' }} >
                        <Box >
                            <h5>Account Details</h5>
                            <List >
                                {
                                    accountRows.length === 0 ? (
                                        <ListItem disablePadding><ListItemButton>
                                            <ListItemText primary={"⚡ Bank account data : N/A"} />
                                        </ListItemButton>
                                        </ListItem>
                                    ) : accountRows.map((item, index) => {
                                        return (
                                            <ListItem disablePadding key={index}><ListItemButton>
                                                <ListItemText primary={`⚡ ${item[0]} : ${item[1]}`} />
                                            </ListItemButton>
                                            </ListItem>
                                        )
                                    })
                                }




                            </List>

                        </Box>


                    </Grid>
                    <Grid item xs={6} >

                        <Box >
                            <h3>Indicators </h3>
                            <List >
                                {indicatorRows.map((item, index) => {
                                    const r = item['rating'];
                                    return (
                                        <Box p={1} key={index}>
                                            <Typography ml={2} mb={1} style={{fontWeight: 'bold'}}> {`${item['name']} (${r.toString()})`}</Typography>
                                            <Progressbar percentage={item['rating']} /></Box>
                                    )
                                })}




                            </List>
                        </Box>


                    </Grid>

                </Grid>
            </Box>
        </div >
    )
}

const DetailSections = ({ application, statusLabel, amountApproved }) => {
    const value = (item) => naValue(item);
    const section = (title, rows) => <div className="report-section"><h3>{title}</h3><div className="report-section-grid">{rows.map(([label, item]) => <div key={label}><span>{label}</span><strong>{value(item)}</strong></div>)}</div></div>;
    return <div className="report-sections">
        {section('Applicant', [['Name', application.name], ['Mobile', application.mobileNumber], ['Email', application.email]])}
        {section('Business', [['Business Name', application.businessName], ['Sector', application.businessSector || application.typeOfBusiness], ['Category', application.businessCategory]])}
        {section('Location', [['Address', application.businessAddress], ['State', application.businessState], ['District', application.businessDistrict], ['Pincode', application.businessPinCode]])}
        {section('Financial', [['Monthly Revenue', naMoney(application.monthlyRevenue)], ['Monthly Transactions', application.monthlyTransactionCount], ['Average Transaction Value', naMoney(application.averageTransactionValue)], ['Digital Payment', application.digitalPaymentPercentage === null || application.digitalPaymentPercentage === undefined ? null : `${application.digitalPaymentPercentage}%`]])}
        {section('Loan', [['Requested Amount', naMoney(application.amountApplied)], ['Purpose', application.purposeOfLoan || application.loanPurpose], ['Tenure', application.tenureMonths ? `${application.tenureMonths} months` : null]])}
        {section('Application Status', [['Status', statusLabel], ['Application Date', application.createdAt ? new Date(application.createdAt).toLocaleDateString() : null]])}
        {section('Admin Decision', [['Approved Amount', naMoney(amountApproved)]])}
    </div>;
}


const FullReport = ({ reportData,reportId }) => {
    const [open, setOpen] = React.useState(false);
    const [deleteOpen, setDeleteOpen] = React.useState(false);
    const [allowedCredit, setAllowedCredit] = React.useState('');
    const [acceptText, setAcceptText] = React.useState('Submit')
    const [rejectText, setRejectText] = React.useState('Reject')
    const [reviewText, setReviewText] = React.useState('Under Review')
    const [deleteText, setDeleteText] = React.useState('Delete application')

    const handleOpen = (data) => {
        setOpen(true);
        // Pre-fills with the eligible amount the scoring engine calculated; the
        // admin can override it before approving.
        setAllowedCredit(data === null || data === undefined ? '' : data)

    }

    // Canonical decision endpoint. status: approve | reject | review.
    // The backend stores applicationStatus + amountApproved.
    const submitDecision = (status, amount, setText, busyText, idleText) => {
        setText(busyText);
        adminApi.post("/api/admin/update-status", {
            userId: reportId,
            status: status,
            approvedAmount: Number(amount) || 0
        })
            .then(() => {
                window.location = '/all-report'
            })
            .catch((err) => {
                const detail = err && err.response && err.response.data ? err.response.data.detail : null;
                window.alert(typeof detail === 'string' ? detail : 'Unable to update the application status.');
                setText(idleText)
            })
    }

    const handleAcceptSubmit = () => {
        // An approval must carry a real sanctioned amount.
        if (!(Number(allowedCredit) > 0)) {
            window.alert('Enter the amount to sanction before approving.');
            return;
        }
        submitDecision('approve', allowedCredit, setAcceptText, 'Submitting...', 'Submit')
    }

    const handleRejectSubmit = () => {
        submitDecision('reject', 0, setRejectText, 'Rejecting...', 'Reject')
    }

    const handleReviewSubmit = () => {
        submitDecision('review', 0, setReviewText, 'Updating...', 'Under Review')
    }

    const handleDelete = () => {
        setDeleteOpen(true);
    }

    const confirmDelete = () => {
        setDeleteText('Deleting...');
        adminApi.delete(`/api/admin/application/${reportId}`).then(() => {
            window.location = '/all-report';
        }).catch((err) => {
            const detail = err && err.response && err.response.data ? err.response.data.detail : null;
            window.alert(typeof detail === 'string' ? detail : 'Unable to delete the application.');
            setDeleteText('Delete application');
            setDeleteOpen(false);
        });
    }


    const handleClose = () => setOpen(false);

    return (
        <>
            <div ref={ref}>
                <Box sx={{ flexGrow: 1 }}>
                    <Grid container spacing={2}>
                        <Grid item xs={3} >
                            <Item direction="column"
                                alignItems="center"
                                justifyContent="center"
                                style={{ minHeight: '100vh' }}>
                                <SideBox data={reportData['userFormSubmittedInfo']} /></Item>
                        </Grid>
                        <Grid item xs={9}>
                            <DetailSections application={reportData.application || {}} statusLabel={reportData.statusLabel} amountApproved={reportData.amountApproved} />
                            <Typography variant="h6" style={{ margin: '24px 0 10px' }}>BizFiz Analysis</Typography>
                            <Item direction="column"
                                alignItems="center"
                                justifyContent="center"
                                style={{ minHeight: '40vh' }}>
                                <MainBox piedata={reportData['transactionalAnalysis']}
                                    score={reportData['score']}
                                    scoreScale={reportData['scoreScale']}
                                    credit={reportData['allowedCredit']}
                                    risk={reportData['riskCategory']}
                                    recommendation={reportData['recommendation']}
                                    requested={reportData['requestedAmount']} />

                            </Item>
                            <br />
                            <Item direction="column"
                                alignItems="center"
                                justifyContent="center"
                                style={{ minHeight: '40vh' }}>
                                <MainBoxSecond
                                    account={reportData['accountDetails']}

                                    indicators={reportData['indicators']}
                                /></Item>
                        </Grid>


                        <Grid item container direction="row" xs={12} style={{ minHeight: '40vh' }}>
                            <Typography pl={6}>Details Parameter Analysis : </Typography>
                            <Grid item container  >
                                {
                                    getIndicatorList(reportData['indicators']).map((item, index) => {
                                        return (
                                            <SectorCard
                                                key={index}
                                                name={item.name}
                                                rating={item.rating}
                                                listTitle={item.listTitle}
                                                list={item.list}


                                            />)
                                    })

                                    // <SectorCard
                                    // name={},rating, listTitle, list
                                }</Grid>
                        </Grid>





                    </Grid>
                </Box>
            </div>
            <Grid
                item xs={12}
                container
                spacing={0}
                direction="column"
                alignItems="center"
                justifyContent="center"
                style={{ minHeight: '30vh' }}
            >

                <Grid container
                    spacing={0}
                    direction="row"
                    alignItems="center"
                    justifyContent="space-evenly" item xs={3}>
                    <Button variant="contained" color="error" onClick={handleRejectSubmit}>
                        {rejectText}
                            </Button>
                     <Button variant="contained" color="warning" onClick={handleReviewSubmit}>
                        {reviewText}
                            </Button>
                    <Button variant="contained" color="success" onClick={() => handleOpen(reportData['allowedCredit'])}>
                        Accept
                            </Button>
                            <Button variant="outlined" color="error" onClick={handleDelete} disabled={deleteText === 'Deleting...'}>{deleteText}</Button>

                </Grid>

            </Grid>

            <Modal
                open={deleteOpen}
                onClose={() => setDeleteOpen(false)}
                aria-labelledby="delete-modal-title"
            >
                <Box sx={style}>
                    <Typography id="delete-modal-title" variant="h6" component="h2">
                        Delete Application?
                    </Typography>
                    <List dense>
                        <ListItem><ListItemText primary="Applicant" secondary={naValue((reportData.application || {}).name)} /></ListItem>
                        <ListItem><ListItemText primary="Business" secondary={naValue((reportData.application || {}).businessName)} /></ListItem>
                        <ListItem><ListItemText primary="Application ID" secondary={reportId} /></ListItem>
                    </List>
                    <Box display="flex" justifyContent="flex-end" gap={1}>
                        <Button variant="outlined" onClick={() => setDeleteOpen(false)} disabled={deleteText === 'Deleting...'}>Cancel</Button>
                        <Button variant="contained" color="error" onClick={confirmDelete} disabled={deleteText === 'Deleting...'}>{deleteText}</Button>
                    </Box>
                </Box>
            </Modal>
            <Modal
                open={open}
                onClose={handleClose}
                aria-labelledby="modal-modal-title"
                aria-describedby="modal-modal-description"
            >
                <Box sx={style}>
                    <Typography id="modal-modal-title" variant="h6" component="h2">
                        Confirm Max Allowed Credit

            <br /><br />
                    </Typography>
                    <TextField id="standard-basic" label="credit" variant="outlined" value={allowedCredit} onChange={(event)=>{setAllowedCredit(event.target.value)}} />
                    <br /><br />
                    <Button variant="contained" color="success" onClick={handleAcceptSubmit}>
                        {acceptText}
                            </Button>
                </Box>
            </Modal>
        </>
    )
}



export default FullReport
