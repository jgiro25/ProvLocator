// Initialize map
const map = L.map('map').setView([37.7749, -122.4194], 13); // Centered on San Francisco

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Dummy provider data
const providers = [
  { name: 'Provider A', lat: 37.7749, lng: -122.4194, info: 'This is Provider A' },
  { name: 'Provider B', lat: 37.7849, lng: -122.4094, info: 'This is Provider B' },
  { name: 'Provider C', lat: 37.7649, lng: -122.4294, info: 'This is Provider C' },
];

// Add markers
providers.forEach(provider => {
  const marker = L.marker([provider.lat, provider.lng]).addTo(map);
  marker.on('click', () => {
    document.getElementById('info-details').textContent = provider.info;
  });
});
