import * as React from 'react';
import {
    PieChart,
    Pie,
    Tooltip,
    ResponsiveContainer,
    Cell
} from 'recharts';

import Button from '@mui/material/Button';
import Modal from '@mui/material/Modal';
import TextField from '@mui/material/TextField';
import Pdf from 'react-to-pdf';

import adminApi from '../../api';
import Progressbar from '../../component/Progressbar';

import './FullReport.css';

const STATUS_LABELS = {
    0: 'Pending',
    1: 'Approved',
    2: 'Under Review',
    3: 'Rejected'
};

const CHART_COLORS = [
    '#4f46e5',
    '#0f766e',
    '#2563eb',
    '#d97706',
    '#dc2626'
];

const modalStyle = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: 'min(92vw, 460px)',
    backgroundColor: '#ffffff',
    border: '1px solid #e2e8f0',
    borderRadius: '18px',
    boxShadow: '0 24px 70px rgba(15, 23, 42, 0.22)',
    padding: '28px'
};

const naValue = (value) => {
    if (value === null || value === undefined || value === '') {
        return 'N/A';
    }

    return value;
};

const naMoney = (value) => {
    if (value === null || value === undefined || value === '') {
        return 'N/A';
    }

    const number = Number(value);

    if (Number.isNaN(number)) {
        return 'N/A';
    }

    return `₹${number.toLocaleString('en-IN')}`;
};

const dateText = (value) => {
    if (!value) {
        return 'N/A';
    }

    const parsed = new Date(value);

    if (Number.isNaN(parsed.getTime())) {
        return 'N/A';
    }

    return parsed.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
};

const scoreText = (score, scale = 100) => {
    if (score === null || score === undefined || score === '') {
        return 'N/A';
    }

    return `${score} / ${scale}`;
};

const statusClass = (label) => {
    return `biz-status biz-status-${String(label || '')
        .toLowerCase()
        .replace(/\s+/g, '-')}`;
};

const getArrayListSector = (data) => {
    return Object.keys(data || {}).map(
        (key) => `${key}: ${data[key]}`
    );
};

const getIndicatorList = (list) => {
    if (!list || list.length < 5) {
        return [];
    }

    return [
        {
            name: list[0]?.name,
            rating: list[0]?.rating,
            listTitle: 'Competitors',
            list: list[0]?.competitors,
            remark: list[0]?.remarks
        },
        {
            name: list[2]?.name,
            rating: list[2]?.rating,
            listTitle: 'Sectors',
            list: getArrayListSector(list[2]?.sectors),
            remark: list[2]?.remark
        },
        {
            name: list[3]?.name,
            rating: list[3]?.rating,
            listTitle: 'More Prosperous Areas',
            list: list[3]?.moreProsperousAreas,
            remark: list[3]?.remark
        },
        {
            name: list[4]?.name,
            rating: list[4]?.rating,
            listTitle: 'Better Areas',
            list: list[4]?.betterAreas,
            remark: list[4]?.remark
        }
    ];
};

function DetailCard({
    number,
    title,
    subtitle,
    rows,
    wide = false
}) {
    return (
        <section className={`biz-card ${wide ? 'biz-card-wide' : ''}`}>
            <div className="biz-card-heading">
                <div className="biz-number">
                    {number}
                </div>

                <div>
                    <h2>{title}</h2>

                    {subtitle ? (
                        <p>{subtitle}</p>
                    ) : null}
                </div>
            </div>

            <div className="biz-fields">
                {rows.map(([label, value]) => (
                    <div
                        className="biz-field"
                        key={label}
                    >
                        <span className="biz-field-label">
                            {label}
                        </span>

                        <strong className="biz-field-value">
                            {naValue(value)}
                        </strong>
                    </div>
                ))}
            </div>
        </section>
    );
}

function RiskIntelligence({ reportData }) {
    const chartData =
        reportData.transactionalAnalysis || [];

    const indicators =
        reportData.indicators || [];

    const accountDetails = Object.entries(
        reportData.accountDetails || {}
    );

    return (
        <section
            className="biz-card biz-card-wide"
            id="bizfiz-analysis"
        >
            <div className="biz-card-heading biz-card-heading-between">
                <div className="biz-card-heading-left">
                    <div className="biz-number">
                        06
                    </div>

                    <div>
                        <span className="biz-kicker">
                            AI DECISION SUPPORT
                        </span>

                        <h2>
                            BizFiz Risk Intelligence
                        </h2>

                        <p>
                            Business and financial
                            intelligence supporting the
                            bank's application review.
                        </p>
                    </div>
                </div>

                <Pdf
                    targetRef={null}
                    options={{
                        orientation: 'landscape',
                        unit: 'in',
                        format: [14, 14]
                    }}
                    filename="bizfiz-report.pdf"
                >
                    {({ toPdf }) => (
                        <Button
                            variant="outlined"
                            size="small"
                            onClick={toPdf}
                            className="biz-pdf-button"
                        >
                            Export PDF
                        </Button>
                    )}
                </Pdf>
            </div>

            <div className="biz-risk-summary">
                <div className="biz-risk-box score">
                    <span>BizFiz Score</span>
                    <strong>
                        {scoreText(
                            reportData.score,
                            reportData.scoreScale || 100
                        )}
                    </strong>
                </div>

                <div className="biz-risk-box risk">
                    <span>Risk Level</span>
                    <strong>
                        {naValue(
                            reportData.riskCategory
                        )}
                    </strong>
                </div>

                <div className="biz-risk-box recommendation">
                    <span>Recommendation</span>
                    <strong>
                        {naValue(
                            reportData.recommendation
                        )}
                    </strong>
                </div>

                <div className="biz-risk-box amount">
                    <span>Eligible Amount</span>
                    <strong>
                        {naMoney(
                            reportData.allowedCredit
                        )}
                    </strong>
                </div>
            </div>

            <div className="biz-analysis-grid">
                <div className="biz-analysis-card">
                    <div className="biz-subheading">
                        <h3>Score Breakdown</h3>
                        <span>
                            Component contribution
                        </span>
                    </div>

                    {chartData.length > 0 ? (
                        <>
                            <ResponsiveContainer
                                width="100%"
                                height={280}
                            >
                                <PieChart>
                                    <Pie
                                        data={chartData}
                                        dataKey="value"
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={55}
                                        outerRadius={95}
                                        paddingAngle={3}
                                        isAnimationActive={false}
                                    >
                                        {chartData.map(
                                            (entry, index) => (
                                                <Cell
                                                    key={`cell-${index}`}
                                                    fill={
                                                        CHART_COLORS[
                                                            index %
                                                                CHART_COLORS.length
                                                        ]
                                                    }
                                                />
                                            )
                                        )}
                                    </Pie>

                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>

                            <div className="biz-chip-list">
                                {chartData.map(
                                    (item) => (
                                        <span
                                            key={
                                                item.name
                                            }
                                        >
                                            {item.name}:{' '}
                                            {item.value}
                                        </span>
                                    )
                                )}
                            </div>
                        </>
                    ) : (
                        <div className="biz-empty">
                            No score breakdown available.
                        </div>
                    )}
                </div>

                <div className="biz-analysis-card">
                    <div className="biz-subheading">
                        <h3>Account Details</h3>
                        <span>
                            Supporting account information
                        </span>
                    </div>

                    {accountDetails.length > 0 ? (
                        <div className="biz-account-list">
                            {accountDetails.map(
                                ([label, value]) => (
                                    <div
                                        className="biz-account-row"
                                        key={label}
                                    >
                                        <span>
                                            {label}
                                        </span>

                                        <strong>
                                            {naValue(
                                                value
                                            )}
                                        </strong>
                                    </div>
                                )
                            )}
                        </div>
                    ) : (
                        <div className="biz-empty">
                            Bank account data: N/A
                        </div>
                    )}
                </div>
            </div>

            <div className="biz-indicator-grid">
                {indicators.map(
                    (item, index) => (
                        <div
                            className="biz-indicator"
                            key={`${item.name || 'indicator'}-${index}`}
                        >
                            <div className="biz-indicator-top">
                                <span>
                                    {naValue(
                                        item.name
                                    )}
                                </span>

                                <strong>
                                    {naValue(
                                        item.rating
                                    )}
                                </strong>
                            </div>

                            <Progressbar
                                percentage={
                                    Number(
                                        item.rating
                                    ) || 0
                                }
                            />
                        </div>
                    )
                )}
            </div>

            <div className="biz-insight-grid">
                {getIndicatorList(
                    indicators
                ).map((item, index) => (
                    <div
                        className="biz-insight"
                        key={`${item.name || 'insight'}-${index}`}
                    >
                        <div className="biz-insight-top">
                            <span>
                                {naValue(
                                    item.name
                                )}
                            </span>

                            <strong>
                                {naValue(
                                    item.rating
                                )}
                            </strong>
                        </div>

                        {item.remark ? (
                            <p>
                                {item.remark}
                            </p>
                        ) : null}

                        {item.list?.length ? (
                            <ul>
                                {item.list
                                    .slice(0, 5)
                                    .map(
                                        (entry) => (
                                            <li
                                                key={entry}
                                            >
                                                {
                                                    entry
                                                }
                                            </li>
                                        )
                                    )}
                            </ul>
                        ) : null}
                    </div>
                ))}
            </div>
        </section>
    );
}

const FullReport = ({
    reportData,
    reportId
}) => {
    const pdfRef = React.useRef(null);

    const [approvalOpen, setApprovalOpen] =
        React.useState(false);

    const [deleteOpen, setDeleteOpen] =
        React.useState(false);

    const [approvedAmount, setApprovedAmount] =
        React.useState('');

    const [acceptText, setAcceptText] =
        React.useState('Approve Application');

    const [rejectText, setRejectText] =
        React.useState('Reject');

    const [reviewText, setReviewText] =
        React.useState('Under Review');

    const [deleteText, setDeleteText] =
        React.useState('Delete Application');

    const application =
        reportData.application || {};

    const statusLabel =
        reportData.statusLabel ||
        STATUS_LABELS[
            application.applicationStatus
        ] ||
        'N/A';

    const requestedAmount =
        application.amountApplied !== null &&
        application.amountApplied !== undefined
            ? application.amountApplied
            : reportData.requestedAmount;

    const amountApproved =
        reportData.amountApproved !== null &&
        reportData.amountApproved !== undefined
            ? reportData.amountApproved
            : application.amountApproved;

    const submitDecision = (
        status,
        amount,
        setText,
        busyText,
        idleText
    ) => {
        setText(busyText);

        adminApi
            .post(
                '/api/admin/update-status',
                {
                    userId: reportId,
                    status,
                    approvedAmount:
                        Number(amount) || 0
                }
            )
            .then(() => {
                window.location =
                    '/all-report';
            })
            .catch((error) => {
                const detail =
                    error?.response?.data
                        ?.detail;

                window.alert(
                    typeof detail ===
                        'string'
                        ? detail
                        : 'Unable to update the application status.'
                );

                setText(idleText);
            });
    };

    const handleApprove = () => {
        if (!(Number(approvedAmount) > 0)) {
            window.alert(
                'Enter the amount to sanction before approving.'
            );
            return;
        }

        submitDecision(
            'approve',
            approvedAmount,
            setAcceptText,
            'Approving...',
            'Approve Application'
        );
    };

    const handleReject = () => {
        submitDecision(
            'reject',
            0,
            setRejectText,
            'Rejecting...',
            'Reject'
        );
    };

    const handleReview = () => {
        submitDecision(
            'review',
            0,
            setReviewText,
            'Updating...',
            'Under Review'
        );
    };

    const confirmDelete = () => {
        setDeleteText('Deleting...');

        adminApi
            .delete(
                `/api/admin/application/${reportId}`
            )
            .then(() => {
                window.location =
                    '/all-report';
            })
            .catch((error) => {
                const detail =
                    error?.response?.data
                        ?.detail;

                window.alert(
                    typeof detail ===
                        'string'
                        ? detail
                        : 'Unable to delete the application.'
                );

                setDeleteText(
                    'Delete Application'
                );

                setDeleteOpen(false);
            });
    };

    return (
        <>
            <div
                className="biz-report-page"
                ref={pdfRef}
            >
                {/* PAGE HEADER */}
                <header className="biz-report-header">
                    <div>
                        <button
                            type="button"
                            className="biz-back-button"
                            onClick={() => {
                                window.location =
                                    '/all-report';
                            }}
                        >
                            ← Back to Applications
                        </button>

                        <span className="biz-kicker">
                            APPLICATION REVIEW
                        </span>

                        <h1>
                            {naValue(
                                application.businessName ||
                                    application.name
                            )}
                        </h1>

                        <p className="biz-application-id">
                            Application ID:{' '}
                            <strong>
                                {naValue(
                                    reportId
                                )}
                            </strong>
                        </p>
                    </div>

                    <div className="biz-header-status">
                        <span
                            className={statusClass(
                                statusLabel
                            )}
                        >
                            {statusLabel}
                        </span>
                    </div>
                </header>

                {/* QUICK SUMMARY */}
                <section className="biz-summary">
                    <div>
                        <span>Applicant</span>
                        <strong>
                            {naValue(
                                application.name
                            )}
                        </strong>
                    </div>

                    <div>
                        <span>Business</span>
                        <strong>
                            {naValue(
                                application.businessName
                            )}
                        </strong>
                    </div>

                    <div>
                        <span>Sector</span>
                        <strong>
                            {naValue(
                                application.businessSector ||
                                    application.typeOfBusiness
                            )}
                        </strong>
                    </div>

                    <div>
                        <span>Requested Amount</span>
                        <strong>
                            {naMoney(
                                requestedAmount
                            )}
                        </strong>
                    </div>
                </section>

                {/* DETAILS */}
                <main className="biz-content-grid">
                    <DetailCard
                        number="01"
                        title="Applicant Information"
                        subtitle="Borrower identity and contact information"
                        rows={[
                            [
                                'Full Name',
                                application.name
                            ],
                            [
                                'Mobile Number',
                                application.mobileNumber
                            ],
                            [
                                'Email Address',
                                application.email
                            ]
                        ]}
                    />

                    <DetailCard
                        number="02"
                        title="Business Information"
                        subtitle="Business profile and classification"
                        rows={[
                            [
                                'Business Name',
                                application.businessName
                            ],
                            [
                                'Business Sector',
                                application.businessSector ||
                                    application.typeOfBusiness
                            ],
                            [
                                'Business Category',
                                application.businessCategory
                            ],
                            [
                                'Years in Business',
                                application.yearsInBusiness
                            ]
                        ]}
                    />

                    <DetailCard
                        number="03"
                        title="Location"
                        subtitle="Business operating location"
                        rows={[
                            [
                                'Business Address',
                                application.businessAddress
                            ],
                            [
                                'State',
                                application.businessState
                            ],
                            [
                                'District',
                                application.businessDistrict
                            ],
                            [
                                'Pincode',
                                application.businessPinCode
                            ]
                        ]}
                    />

                    <DetailCard
                        number="04"
                        title="Financial Information"
                        subtitle="Business financial indicators"
                        rows={[
                            [
                                'Monthly Revenue',
                                naMoney(
                                    application.monthlyRevenue
                                )
                            ],
                            [
                                'Monthly Transactions',
                                application.monthlyTransactionCount
                            ],
                            [
                                'Average Transaction Value',
                                naMoney(
                                    application.averageTransactionValue
                                )
                            ],
                            [
                                'Digital Payment',
                                application.digitalPaymentPercentage ===
                                    null ||
                                application.digitalPaymentPercentage ===
                                    undefined
                                    ? 'N/A'
                                    : `${application.digitalPaymentPercentage}%`
                            ]
                        ]}
                    />

                    <DetailCard
                        number="05"
                        title="Loan Request"
                        subtitle="Requested financing information"
                        wide
                        rows={[
                            [
                                'Requested Amount',
                                naMoney(
                                    requestedAmount
                                )
                            ],
                            [
                                'Purpose',
                                application.purposeOfLoan ||
                                    application.loanPurpose
                            ],
                            [
                                'Tenure',
                                application.tenureMonths
                                    ? `${application.tenureMonths} months`
                                    : 'N/A'
                            ],
                            [
                                'Approved Amount',
                                naMoney(
                                    amountApproved
                                )
                            ]
                        ]}
                    />

                    <RiskIntelligence
                        reportData={reportData}
                    />

                    <DetailCard
                        number="07"
                        title="Application Status"
                        subtitle="Current state of the loan application"
                        rows={[
                            [
                                'Current Status',
                                statusLabel
                            ],
                            [
                                'Application Date',
                                dateText(
                                    application.applicationDate ||
                                        application.createdAt
                                )
                            ],
                            [
                                'Requested Amount',
                                naMoney(
                                    requestedAmount
                                )
                            ],
                            [
                                'Approved Amount',
                                naMoney(
                                    amountApproved
                                )
                            ]
                        ]}
                    />

                    <section className="biz-card biz-card-wide biz-decision-card">
                        <div className="biz-card-heading">
                            <div className="biz-number">
                                08
                            </div>

                            <div>
                                <span className="biz-kicker">
                                    BANK REVIEW
                                </span>

                                <h2>
                                    Admin Decision
                                </h2>

                                <p>
                                    Record the bank's
                                    decision for this
                                    application.
                                </p>
                            </div>
                        </div>

                        <div className="biz-decision-summary">
                            <div>
                                <span>
                                    Current Status
                                </span>

                                <strong>
                                    {statusLabel}
                                </strong>
                            </div>

                            <div>
                                <span>
                                    Approved Amount
                                </span>

                                <strong>
                                    {naMoney(
                                        amountApproved
                                    )}
                                </strong>
                            </div>
                        </div>

                        <div className="biz-decision-actions">
                            <Button
                                variant="contained"
                                color="success"
                                onClick={() => {
                                    setApprovedAmount(
                                        reportData.allowedCredit ||
                                            ''
                                    );

                                    setApprovalOpen(
                                        true
                                    );
                                }}
                            >
                                {acceptText}
                            </Button>

                            <Button
                                variant="contained"
                                color="warning"
                                onClick={handleReview}
                            >
                                {reviewText}
                            </Button>

                            <Button
                                variant="contained"
                                color="error"
                                onClick={handleReject}
                            >
                                {rejectText}
                            </Button>

                            <Button
                                variant="outlined"
                                color="error"
                                onClick={() =>
                                    setDeleteOpen(
                                        true
                                    )
                                }
                            >
                                {deleteText}
                            </Button>
                        </div>
                    </section>
                </main>
            </div>

            {/* APPROVAL MODAL */}
            <Modal
                open={approvalOpen}
                onClose={() =>
                    setApprovalOpen(false)
                }
            >
                <div style={modalStyle}>
                    <div className="biz-modal-badge approval">
                        ₹
                    </div>

                    <h2 className="biz-modal-title">
                        Confirm Loan Approval
                    </h2>

                    <p className="biz-modal-copy">
                        Enter the final amount to
                        sanction for this borrower.
                    </p>

                    <TextField
                        fullWidth
                        label="Approved Amount"
                        type="number"
                        value={
                            approvedAmount
                        }
                        onChange={(event) =>
                            setApprovedAmount(
                                event.target
                                    .value
                            )
                        }
                    />

                    <div className="biz-modal-actions">
                        <Button
                            variant="outlined"
                            onClick={() =>
                                setApprovalOpen(
                                    false
                                )
                            }
                        >
                            Cancel
                        </Button>

                        <Button
                            variant="contained"
                            color="success"
                            onClick={
                                handleApprove
                            }
                        >
                            Approve
                        </Button>
                    </div>
                </div>
            </Modal>

            {/* DELETE MODAL */}
            <Modal
                open={deleteOpen}
                onClose={() =>
                    setDeleteOpen(false)
                }
            >
                <div style={modalStyle}>
                    <div className="biz-modal-badge delete">
                        !
                    </div>

                    <h2 className="biz-modal-title">
                        Delete Application?
                    </h2>

                    <p className="biz-modal-copy">
                        This will permanently remove
                        the selected borrower
                        application and its linked
                        analysis.
                    </p>

                    <div className="biz-modal-details">
                        <div>
                            <span>
                                Applicant
                            </span>
                            <strong>
                                {naValue(
                                    application.name
                                )}
                            </strong>
                        </div>

                        <div>
                            <span>
                                Business
                            </span>
                            <strong>
                                {naValue(
                                    application.businessName
                                )}
                            </strong>
                        </div>

                        <div>
                            <span>
                                Application ID
                            </span>
                            <strong>
                                {naValue(
                                    reportId
                                )}
                            </strong>
                        </div>
                    </div>

                    <div className="biz-modal-actions">
                        <Button
                            variant="outlined"
                            onClick={() =>
                                setDeleteOpen(
                                    false
                                )
                            }
                            disabled={
                                deleteText ===
                                'Deleting...'
                            }
                        >
                            Cancel
                        </Button>

                        <Button
                            variant="contained"
                            color="error"
                            onClick={
                                confirmDelete
                            }
                            disabled={
                                deleteText ===
                                'Deleting...'
                            }
                        >
                            Delete
                        </Button>
                    </div>
                </div>
            </Modal>
        </>
    );
};

export default FullReport;