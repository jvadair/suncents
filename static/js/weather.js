function getCoordinates() {
    return new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
            position => resolve(position.coords),
            error => reject(error)
        )
    })
}

// NOTE: Doesn't work due to CORS
// async function getUTCOffset(coords) {
//     const {latitude, longitude} = coords;
//     const res = await fetch(`https://timeapi.io/api/TimeZone/coordinate?latitude=${latitude}&longitude=${longitude}`);
//     return parseInt(await res.json()["currentUtcOffset"]["seconds"]);
// }


async function getSunDownTime(coords) {
    const {latitude, longitude} = coords;
    // Query sunrise-sunset API
    const res = await fetch(`https://secure.geonames.org/timezoneJSON?username=suncents&lat=${latitude}&lng=${longitude}`);
    const data = await res.json();
    const sunsetTime = data["sunset"];
    return sunsetTime.split(" ")[1];
}

async function getLocationData(coords) {
    const {latitude, longitude} = coords;
    const res = await fetch(`https://api.weather.gov/points/${latitude},${longitude}`);
    return await res.json();
}

async function getForecastData(locationData) {
    const res = await fetch(locationData["properties"]["forecast"]);
    return await res.json();
}
