
export function openRulesModal() {
    document.getElementById("rulesModal").style.display = "flex";
}

export function closeRulesModal() {
    document.getElementById("rulesModal").style.display = "none";
}

export function openIncomeModal() {
    document.getElementById("incomeModal").style.display = "flex";
}

export function closeIncomeModal() {
    document.getElementById("incomeModal").style.display = "none";
}

export async function switchRulesLang(label) {
    let language = "english";
    if (label.includes("繁體")) language = "traditional";
    if (label.includes("简体")) language = "simplified";

    const rules = await fetch(`http://127.0.0.1:8080/api/rules/${language}`); // Must use backticks.
    document.getElementById("rulesContent").innerText = await rules.text();
}
