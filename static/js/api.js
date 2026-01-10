
export async function loadHomeConfig() {
    const response = await fetch('http://127.0.0.1:8080/api/home_config');
    const json = await response.json();
    return json;
}
