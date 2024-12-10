// Initialize map
const radiusMap = L.map('radius-map').setView([37.7749, -122.4194], 13);

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(radiusMap);

// Dummy provider data
const providers = [
  { name: 'Provider A', lat: 37.7749, lng: -122.4194 },
  { name: 'Provider B', lat: 37.7849, lng: -122.4094 },
  { name: 'Provider C', lat: 37.7649, lng: -122.4294 },
];

// Handle radius form submission
document.getElementById('radius-form').addEventListener('submit', e => {
  e.preventDefault();
  const radius = parseFloat(document.getElementById('radius').value);

  if (isNaN(radius)) return alert('Please enter a valid radius.');

  radiusMap.eachLayer(layer => {
    if (layer instanceof L.Circle) {
      radiusMap.removeLayer(layer);
    }
  });

  const center = radiusMap.getCenter();
  const milesToMeters = radius * 1609.34;

  const circle = L.circle([center.lat, center.lng], {
    radius: milesToMeters,
    color: 'blue',
    fillOpacity: 0.2,
  }).addTo(radiusMap);

  providers.forEach(provider => {
    const distance = radiusMap.distance(center, [provider.lat, provider.lng]);
    if (distance <= milesToMeters) {
      L.marker([provider.lat, provider.lng]).addTo(radiusMap);
    }
  });
});
