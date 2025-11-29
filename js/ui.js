
document.getElementById("resetPlayerBtn").addEventListener("click", () => {
    document.getElementById("playerNameInput").value = "";
    document.getElementById("playerCapitalInput").value = "";
});

document.getElementById("submitPlayerBtn").addEventListener("click", () => {
    const name = document.getElementById("playerNameInput").value.trim();
    const capital = Number(document.getElementById("playerCapitalInput").value);

    if (!name) return alert("Please type your name 🙏");

    if (!Number.isInteger(capital) || capital < 300 || capital > 1_000_000_000)
        return alert("🪙 Capital must be integer between 300 and 1,000,000,000!");

    // Save to your state.js.
    window.gameState.playerName = name;
    window.gameState.capital = capital;

    alert(`Welcome, ${name}! Your starting capital: $${capital}`);
});
