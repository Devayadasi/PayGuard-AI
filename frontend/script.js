
const API_URL = "http://127.0.0.1:8000";

let decisionChart = null;
let lastTransactionId = null;


// ==================================================
// 1. SAFE HTML OUTPUT
// ==================================================

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}


// ==================================================
// 2. PAGE NAVIGATION
// ==================================================

function showPage(page) {

    document.querySelectorAll(".page").forEach(section => {
        section.classList.add("hidden");
    });

    document.getElementById(`${page}Page`).classList.remove("hidden");

    document.querySelectorAll(".nav-item").forEach(button => {
        button.classList.toggle(
            "active",
            button.dataset.page === page
        );
    });

    closeExplanation();

    if (page === "overview") {
        loadDashboard();
    }

    if (page === "history" || page === "analyze") {
        loadTransactions();
    }
}


document.querySelectorAll(".nav-item").forEach(button => {

    button.addEventListener("click", () => {
        showPage(button.dataset.page);
    });

});


// ==================================================
// 3. FORMAT HELPERS
// ==================================================

function formatAmount(amount) {

    return Number(amount).toLocaleString("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2
    });

}


function formatDate(date) {

    return date ? new Date(date).toLocaleString("en-IN") : "—";

}


function decisionBadge(decision) {

    return `
        <span class="decision-badge ${escapeHTML(decision)}">
            ${escapeHTML(decision)}
        </span>
    `;

}


// ==================================================
// 4. DASHBOARD STATISTICS
// ==================================================

async function loadDashboard() {

    try {

        const response = await fetch(`${API_URL}/api/stats`);

        if (!response.ok) {
            throw new Error("Could not load dashboard statistics");
        }

        const data = await response.json();

        document.getElementById("totalTransactions").textContent =
            data.total_transactions;

        document.getElementById("approvedTransactions").textContent =
            data.approved;

        document.getElementById("reviewTransactions").textContent =
            data.under_review;

        document.getElementById("blockedTransactions").textContent =
            data.blocked;

        document.getElementById("averageRisk").textContent =
            Number(data.average_risk_score).toFixed(1);

        const risk = Math.min(
            100,
            Math.max(0, Number(data.average_risk_score))
        );

        document.getElementById("riskCircle").style.borderColor =
            risk >= 70 ? "#e34d5b" :
            risk >= 30 ? "#df8b28" :
            "#0d9b70";

        updateDecisionChart(data);

        await loadTransactions();

    } catch (error) {

        console.error("Dashboard error:", error);

    }

}


// ==================================================
// 5. DECISION CHART
// ==================================================

function updateDecisionChart(data) {

    const canvas = document.getElementById("decisionChart");

    if (!canvas) return;

    if (decisionChart) {
        decisionChart.destroy();
    }

    decisionChart = new Chart(canvas, {

        type: "doughnut",

        data: {

            labels: ["Approved", "Under Review", "Blocked"],

            datasets: [{

                data: [
                    data.approved,
                    data.under_review,
                    data.blocked
                ],

                backgroundColor: [
                    "#0d9b70",
                    "#df8b28",
                    "#e34d5b"
                ],

                borderWidth: 0

            }]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            plugins: {

                legend: {
                    position: "bottom"
                }

            }

        }

    });

}


// ==================================================
// 6. TRANSACTION HISTORY
// ==================================================

async function loadTransactions() {

    try {

        const response = await fetch(
            `${API_URL}/api/transactions?limit=100`
        );

        if (!response.ok) {
            throw new Error("Could not load transactions");
        }

        const transactions = await response.json();

        const recentBody = document.getElementById(
            "recentTransactions"
        );

        const analyzeBody = document.getElementById(
            "analyzeRecentTransactions"
        );

        const historyBody = document.getElementById(
            "historyTransactions"
        );

        const recentRows = transactions.slice(0, 5);

        recentBody.innerHTML = renderTransactions(
            recentRows,
            false
        );

        analyzeBody.innerHTML = renderTransactions(
            transactions.slice(0, 5),
            false
        );

        historyBody.innerHTML = renderTransactions(
            transactions,
            true
        );

    } catch (error) {

        console.error("Transaction history error:", error);

    }

}


function renderTransactions(transactions, showStep) {

    if (!transactions.length) {

        return `
            <tr>
                <td colspan="${showStep ? 8 : 7}">
                    No transactions found.
                </td>
            </tr>
        `;

    }

    return transactions.map(transaction => {

        return `

            <tr>

                <td>#${transaction.id}</td>

                ${showStep ? `<td>${transaction.step}</td>` : ""}

                <td>${escapeHTML(transaction.type)}</td>

                <td>${formatAmount(transaction.amount)}</td>

                <td>
                    ${Number(transaction.risk_score).toFixed(2)}/100
                </td>

                <td>${decisionBadge(transaction.decision)}</td>

                <td>${formatDate(transaction.created_at)}</td>

                <td>
                    <button
                        class="explain-button"
                        onclick="explainTransaction(${Number(transaction.id)})">
                        Explain
                    </button>
                </td>

            </tr>

        `;

    }).join("");

}


// ==================================================
// 7. ANALYZE TRANSACTION
// ==================================================

document.getElementById("transactionForm").addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();

        const button = document.getElementById("analyzeButton");

        button.disabled = true;
        button.textContent = "Analyzing...";

        const transaction = {

            step: Number(document.getElementById("step").value),

            type: document.getElementById("type").value,

            amount: Number(document.getElementById("amount").value),

            oldbalanceOrg: Number(
                document.getElementById("oldbalanceOrg").value
            ),

            oldbalanceDest: Number(
                document.getElementById("oldbalanceDest").value
            )

        };

        try {

            const response = await fetch(`${API_URL}/api/predict`, {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(transaction)

            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Prediction failed");
            }

            lastTransactionId = data.transaction_id;

            document.getElementById("analysisResult")
                .classList.remove("hidden");

            document.getElementById("resultDecision").textContent =
                data.decision;

            document.getElementById("resultDecision").className =
                `decision-badge ${data.decision}`;

            document.getElementById("resultRisk").textContent =
                `${data.risk_score}/100`;

            document.getElementById("resultProbability").textContent =
                `${(data.fraud_probability * 100).toFixed(2)}%`;

            document.getElementById("resultId").textContent =
                `#${data.transaction_id}`;

            document.getElementById("resultMessage").textContent =
                data.message;

            document.getElementById("analysisResult")
                .scrollIntoView({
                    behavior: "smooth",
                    block: "nearest"
                });

            await loadDashboard();

        } catch (error) {

            alert(error.message);

        } finally {

            button.disabled = false;
            button.textContent = "Analyze Transaction →";

        }

    }
);


// ==================================================
// 8. EXPLAIN THIS TRANSACTION BUTTON
// ==================================================

document.getElementById("explainResultButton")
    .addEventListener("click", () => {

        if (lastTransactionId !== null) {
            explainTransaction(lastTransactionId);
        }

    });


// ==================================================
// 9. SHAP EXPLAINABILITY
// ==================================================

async function explainTransaction(transactionId) {

    const panel = document.getElementById("explanationPanel");

    const featuresContainer = document.getElementById("shapFeatures");

    panel.classList.remove("hidden");

    panel.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

    featuresContainer.textContent =
        "Calculating SHAP contributions...";

    try {

        const response = await fetch(
            `${API_URL}/api/explain/${transactionId}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Unable to generate explanation"
            );
        }

        document.getElementById("explainTransactionId").textContent =
            `#${data.transaction_id}`;

        document.getElementById("explainDecision").textContent =
            data.decision;

        document.getElementById("explainDecision").style.color =
            data.decision === "BLOCK" ? "#e34d5b" :
            data.decision === "REVIEW" ? "#df8b28" :
            "#0d9b70";

        document.getElementById("explainRisk").textContent =
            `${Number(data.risk_score).toFixed(2)}/100`;

        document.getElementById("explanationSubtitle").textContent =
            `SHAP explanation for transaction #${data.transaction_id}`;

        const explanations = data.explanations;

        const maxContribution = Math.max(
            ...explanations.map(item =>
                Math.abs(Number(item.contribution))
            ),
            0.000001
        );

        featuresContainer.innerHTML = explanations.map(item => {

            const value = Number(item.contribution);

            const positive = value > 0;

            const width = Math.max(
                1,
                (Math.abs(value) / maxContribution) * 100
            );

            const impactClass = positive ? "positive" : "negative";

            return `

                <div class="shap-feature">

                    <div class="shap-feature-top">

                        <span class="shap-feature-name">
                            ${escapeHTML(item.feature)}
                        </span>

                        <span class="shap-feature-value ${impactClass}">
                            ${value > 0 ? "+" : ""}${value.toFixed(6)}
                        </span>

                    </div>

                    <div class="shap-bar-track">

                        <div
                            class="shap-bar ${impactClass}"
                            style="width: ${width}%">
                        </div>

                    </div>

                    <span class="shap-impact">
                        ${escapeHTML(item.impact)}
                    </span>

                </div>

            `;

        }).join("");

    } catch (error) {

        featuresContainer.textContent = error.message;

    }

}


// ==================================================
// 10. CLOSE EXPLANATION PANEL
// ==================================================

function closeExplanation() {

    document.getElementById("explanationPanel")
        .classList.add("hidden");

}


// ==================================================
// 11. INITIALIZE APPLICATION
// ==================================================

document.addEventListener("DOMContentLoaded", () => {

    loadDashboard();

});
