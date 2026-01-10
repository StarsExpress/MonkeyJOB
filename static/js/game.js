
window.addEventListener("DOMContentLoaded", () => {
    const name = localStorage.getItem("player_name") || "Player";
    const capital = localStorage.getItem("capital") || 0;

    document.getElementById("playerName").innerText = name;
    document.getElementById("playerCapital").innerText = capital;

    // Betting slider.
    const slider = document.getElementById("betSlider");
    const display = document.getElementById("betValue");
    slider.oninput = () => display.innerText = slider.value;
});
