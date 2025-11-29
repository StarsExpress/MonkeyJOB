
export async function loadHomeConfig() {
    const config = await fetch('http://127.0.0.1:8080/api/home_config');
    return await config.json();
}
