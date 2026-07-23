    var API_BASE = '/api';

    var Autocomplete = (function() {
        var GEOCODER = 'https://nominatim.openstreetmap.org/search';
        var DEBOUNCE_MS = 250;
        var MIN_CHARS = 2;
        var MAX_RESULTS = 5;

        function debounce(fn, ms) {
            var id;
            return function() {
                var ctx = this, args = arguments;
                clearTimeout(id);
                id = setTimeout(function() { fn.apply(ctx, args); }, ms);
            };
        }

        function create(inputId, dropdownId, opts) {
            var input = document.getElementById(inputId);
            var dropdown = document.getElementById(dropdownId);
            var items = [];
            var highlightIdx = -1;
            var isOpen = false;
            var currentQuery = '';

            var showCurrentLocation = opts && opts.showCurrentLocation;
            var onSelect = opts && opts.onSelect;

            function renderCurrentLocation() {
                return '<div class="autocomplete-current-location" data-type="current-location">' +
                    '<div class="ac-cl-icon">' +
                        '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">' +
                            '<circle cx="12" cy="12" r="3"/>' +
                            '<path d="M12 2v4m0 12v4M2 12h4m12 0h4"/>' +
                        '</svg>' +
                    '</div>' +
                    '<div>' +
                        '<div class="ac-cl-text">Current location</div>' +
                        '<div class="ac-cl-sub">Use your GPS position</div>' +
                    '</div>' +
                '</div>';
            }

            function renderLoading() {
                return '<div class="autocomplete-loading">' +
                    '<div class="autocomplete-spinner"></div>' +
                    'Searching...' +
                '</div>';
            }

            function renderNoResults() {
                return '<div class="autocomplete-no-results">No results found</div>';
            }

            function renderItem(feature, idx) {
                var addr = feature.address || {};
                var primary = feature.name || feature.display_name.split(',')[0];
                var street = addr.road || addr.pedestrian || addr.suburb || '';
                var city = addr.city || addr.town || addr.village || '';
                var secondary = [street, city, addr.state, addr.country]
                    .filter(Boolean).join(', ');
                if (secondary === primary) secondary = '';

                return '<div class="autocomplete-item" data-index="' + idx + '" role="option">' +
                    '<div class="autocomplete-item-icon">' +
                        '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">' +
                            '<path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>' +
                            '<circle cx="12" cy="9" r="2.5"/>' +
                        '</svg>' +
                    '</div>' +
                    '<div class="autocomplete-item-text">' +
                        '<div class="autocomplete-item-primary">' + escapeHtml(primary) + '</div>' +
                        (secondary ? '<div class="autocomplete-item-secondary">' + escapeHtml(secondary) + '</div>' : '') +
                    '</div>' +
                '</div>';
            }

            function escapeHtml(str) {
                var div = document.createElement('div');
                div.textContent = str;
                return div.innerHTML;
            }

            function render() {
                var html = '';
                if (showCurrentLocation) html += renderCurrentLocation();
                if (isOpen) {
                    if (items.length === 0) {
                        html += renderNoResults();
                    } else {
                        items.forEach(function(feat, i) { html += renderItem(feat, i); });
                    }
                }
                dropdown.innerHTML = html;
                dropdown.classList.toggle('active', isOpen && (items.length > 0 || showCurrentLocation));
                highlightIdx = -1;
                updateHighlight();
            }

            function updateHighlight() {
                var allItems = dropdown.querySelectorAll('.autocomplete-item');
                allItems.forEach(function(el, i) {
                    el.classList.toggle('highlighted', i === highlightIdx);
                });
            }

            function open() {
                isOpen = true;
                input.setAttribute('aria-expanded', 'true');
                render();
            }

            function close() {
                isOpen = false;
                items = [];
                highlightIdx = -1;
                dropdown.innerHTML = '';
                dropdown.classList.remove('active');
                input.setAttribute('aria-expanded', 'false');
            }

            function selectItem(idx) {
                var feat = items[idx];
                if (!feat) return;
                var addr = feat.address || {};
                var lat = parseFloat(feat.lat);
                var lon = parseFloat(feat.lon);
                var primary = feat.name || feat.display_name.split(',')[0];
                var street = addr.road || addr.pedestrian || addr.suburb || '';
                var city = addr.city || addr.town || addr.village || '';
                var secondary = [street, city, addr.state, addr.country]
                    .filter(Boolean).join(', ');
                var label = secondary ? primary + ', ' + secondary : primary;
                input.value = label;
                close();
                if (onSelect) onSelect({ lat: lat, lon: lon, label: label, properties: feat });
            }

            function selectCurrentLocation() {
                input.value = 'Current location';
                close();
                if (opts && opts.onCurrentLocation) opts.onCurrentLocation();
            }

            var fetchSuggestions = debounce(function(query) {
                currentQuery = query;
                if (query.length < MIN_CHARS) { items = []; close(); return; }
                dropdown.innerHTML = (showCurrentLocation ? renderCurrentLocation() : '') + renderLoading();
                dropdown.classList.add('active');
                isOpen = true;
                var params = 'format=jsonv2&limit=' + MAX_RESULTS + '&addressdetails=1&q=' + encodeURIComponent(query);
                fetch(GEOCODER + '?' + params, { headers: { 'Accept': 'application/json' } })
                .then(function(res) { if (!res.ok) throw new Error('Geocoding failed'); return res.json(); })
                .then(function(data) {
                    if (currentQuery !== query) return;
                    items = (data || []).filter(function(f) { return f && f.lat && f.lon && f.display_name; });
                    render();
                })
                .catch(function() { if (currentQuery !== query) return; items = []; render(); });
            }, DEBOUNCE_MS);

            input.addEventListener('input', function() { fetchSuggestions(this.value); });
            input.addEventListener('focus', function() {
                if (this.value.length >= MIN_CHARS && items.length > 0) { isOpen = true; render(); }
            });
            input.addEventListener('keydown', function(e) {
                if (!isOpen) return;
                var totalItems = items.length + (showCurrentLocation ? 1 : 0);
                if (e.key === 'ArrowDown') { e.preventDefault(); highlightIdx = Math.min(highlightIdx + 1, totalItems - 1); updateHighlight(); }
                else if (e.key === 'ArrowUp') { e.preventDefault(); highlightIdx = Math.max(highlightIdx - 1, 0); updateHighlight(); }
                else if (e.key === 'Enter') {
                    e.preventDefault();
                    if (highlightIdx === 0 && showCurrentLocation) selectCurrentLocation();
                    else if (highlightIdx >= 0) selectItem(showCurrentLocation ? highlightIdx - 1 : highlightIdx);
                } else if (e.key === 'Escape') { e.preventDefault(); close(); }
            });
            document.addEventListener('mousedown', function(e) {
                if (!input.contains(e.target) && !dropdown.contains(e.target)) close();
            });
            dropdown.addEventListener('mousedown', function(e) {
                var target = e.target.closest('.autocomplete-item, .autocomplete-current-location');
                if (!target) return;
                e.preventDefault();
                if (target.dataset.type === 'current-location') selectCurrentLocation();
                else selectItem(parseInt(target.dataset.index));
            });

            return { close: close, setValue: function(v) { input.value = v; }, getValue: function() { return input.value; } };
        }
        return { create: create };
    })();

    document.addEventListener('DOMContentLoaded', function() {
        var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        var toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container';
            toastContainer.setAttribute('aria-live', 'polite');
            document.body.appendChild(toastContainer);
        }
        function showToast(message, duration) {
            var toast = document.createElement('div');
            toast.className = 'toast-notification';
            toast.textContent = message;
            toastContainer.appendChild(toast);
            setTimeout(function() {
                toast.classList.add('toast-fade-out');
                setTimeout(function() { if (toast.parentNode) toast.parentNode.removeChild(toast); }, prefersReducedMotion ? 0 : 300);
            }, duration || 3000);
        }

        var routeLayers = [];
        var currentRoutes = [];
        var selectedRouteType = null;
        var routeOriginalText = '';
        var findRoutesBtn = document.getElementById('findRoutesBtn');
        routeOriginalText = findRoutesBtn ? findRoutesBtn.textContent : 'Find Safe Routes';

        var map = L.map('map', { center: [28.6139, 77.2090], zoom: 13, zoomControl: true });
        L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>',
            subdomains: 'abcd', maxZoom: 20
        }).addTo(map);
        map.zoomControl.setPosition('topleft');

        var currentLat = null, currentLon = null, currentMarker = null, accuracyCircle = null;

        var departureTimeInput = document.getElementById('departureTime');
        departureTimeInput.value = formatDateTimeLocal(new Date());
        var timeManuallySet = false;
        departureTimeInput.addEventListener('input', function() { timeManuallySet = true; });

        document.getElementById('nowBtn').addEventListener('click', function() {
            departureTimeInput.value = formatDateTimeLocal(new Date());
            timeManuallySet = false;
        });

        var fromAC = Autocomplete.create('fromInput', 'fromDropdown', {
            showCurrentLocation: true,
            onSelect: function(result) {
                window.selectedFrom = { lat: result.lat, lon: result.lon };
                map.setView([result.lat, result.lon], 15);
            },
            onCurrentLocation: function() { getCurrentLocation(); }
        });

        var toAC = Autocomplete.create('toInput', 'toDropdown', {
            showCurrentLocation: true,
            onSelect: function(result) {
                window.selectedTo = { lat: result.lat, lon: result.lon };
                map.setView([result.lat, result.lon], 15);
            },
            onCurrentLocation: function() { getCurrentLocation(); }
        });

        document.getElementById('gpsBtn').addEventListener('click', function() { getCurrentLocation(); });

        function getCurrentLocation() {
            if (!navigator.geolocation) { showToast('Geolocation is not supported.'); return; }
            var fromInput = document.getElementById('fromInput');
            fromInput.value = 'Getting location...';
            fromInput.disabled = true;
            navigator.geolocation.getCurrentPosition(
                function(pos) {
                    currentLat = pos.coords.latitude;
                    currentLon = pos.coords.longitude;
                    fromInput.value = 'Current location';
                    fromInput.disabled = false;
                    window.selectedFrom = { lat: currentLat, lon: currentLon };
                    map.setView([currentLat, currentLon], 15);
                    if (currentMarker) { currentMarker.setLatLng([currentLat, currentLon]); }
                    else {
                        currentMarker = L.circleMarker([currentLat, currentLon], {
                            radius: 8, fillColor: '#4285F4', fillOpacity: 1, color: '#fff', weight: 3, opacity: 1
                        }).addTo(map);
                    }
                    if (accuracyCircle) map.removeLayer(accuracyCircle);
                    accuracyCircle = L.circleMarker([currentLat, currentLon], {
                        radius: pos.coords.accuracy || 50, fillColor: '#4285F4', fillOpacity: 0.1, color: '#4285F4', weight: 1, opacity: 0.3
                    }).addTo(map);
                },
                function(err) {
                    fromInput.value = ''; fromInput.disabled = false;
                    showToast(err.code === 1 ? 'Location access denied.' : 'Unable to get location.');
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
            );
        }

        if (navigator.geolocation) {
            navigator.permissions.query({ name: 'geolocation' }).then(function(status) {
                if (status.state === 'granted') getCurrentLocation();
            }).catch(function() {});
        }

        findRoutesBtn.addEventListener('click', function(e) {
            if (e && typeof e.preventDefault === 'function') e.preventDefault();

            var from = document.getElementById('fromInput').value;
            var to = document.getElementById('toInput').value;
            if (!from.trim() || !to.trim()) { showToast('Please enter both starting point and destination.'); return; }
            if (!window.selectedFrom || !window.selectedTo) { showToast('Please select locations from the dropdown suggestions.'); return; }

            findRoutesBtn.disabled = true;
            findRoutesBtn.textContent = 'Analyzing Risk & Routes...';

            selectedRouteType = null;

            var slat = window.selectedFrom.lat;
            var slon = window.selectedFrom.lon;

            fetch(API_BASE + '/risk?lat=' + slat + '&lon=' + slon)
            .then(function(res) { if (!res.ok) throw new Error('Risk API error: ' + res.status); return res.json(); })
            .then(function(riskData) {
                updateDashboard(riskData);
                return fetch(API_BASE + '/safe_route?olat=' + slat + '&olon=' + slon + '&dlat=' + window.selectedTo.lat + '&dlon=' + window.selectedTo.lon);
            })
            .then(function(res) { if (!res.ok) throw new Error('Route API error: ' + res.status); return res.json(); })
            .then(function(routeData) {
                if (routeData && routeData.routes && routeData.routes.length > 0) {
                    currentRoutes = routeData.routes;
                    updateRouteCards(routeData.routes);
                    drawRoutesOnMap(routeData.routes);

                    var safestCard = document.querySelector('.safest-card');
                    if (safestCard && !safestCard.classList.contains('unavailable')) {
                        selectRoute(safestCard);
                    }

                    var resultsSection = document.getElementById('insights');
                    if (resultsSection) resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                } else {
                    showToast('No routes found for this journey.');
                }
            })
            .catch(function(err) {
                console.error('Error:', err);
                showToast('Could not fetch route details. Please try again.');
            })
            .finally(function() {
                findRoutesBtn.disabled = false;
                findRoutesBtn.textContent = routeOriginalText;
            });
        });

        function selectRoute(card) {
            if (!card) return;
            if (card.classList.contains('unavailable')) { showUnavailablePopup(card); return; }

            var allCards = document.querySelectorAll('.route-card-inner');
            var routeType = null;
            if (card.classList.contains('safest-card')) routeType = 'safest';
            else if (card.classList.contains('balanced-card')) routeType = 'balanced';
            else if (card.classList.contains('fastest-card')) routeType = 'fastest';

            if (card.classList.contains('selected')) {
                card.classList.remove('selected');
                allCards.forEach(function(c) {
                    if (!c.classList.contains('unavailable')) { c.style.opacity = ''; c.style.pointerEvents = ''; }
                });
                resetRouteHighlight();
                return;
            }

            allCards.forEach(function(c) {
                c.classList.remove('selected');
                if (!c.classList.contains('unavailable')) c.style.opacity = '0.4';
            });
            card.classList.add('selected');
            card.style.opacity = '1';
            card.style.pointerEvents = 'auto';

            highlightRouteOnMap(routeType);

            var route = currentRoutes.find(function(r) { return r.route_type === routeType; });
            if (route) updateDashboardForRoute(route);

            if (window.innerWidth <= 768) {
                card.scrollIntoView({ behavior: prefersReducedMotion ? 'auto' : 'smooth', block: 'center' });
            }
        }

        var routeCards = document.querySelectorAll('.route-card-inner');
        routeCards.forEach(function(card) {
            card.addEventListener('click', function() { selectRoute(this); });
            card.setAttribute('tabindex', '0');
            card.setAttribute('role', 'button');
            card.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectRoute.call(this, this); }
            });
        });

        function showUnavailablePopup(card) {
            var routeType = 'Safest';
            if (card.classList.contains('balanced-card')) routeType = 'Balanced';
            if (card.classList.contains('fastest-card')) routeType = 'Fastest';
            var overlay = document.querySelector('.coming-soon-overlay');
            if (overlay) {
                var title = overlay.querySelector('.coming-soon-title');
                var text = overlay.querySelector('.coming-soon-text');
                if (title) title.textContent = routeType + ' Route Unavailable';
                if (text) text.textContent = 'Sorry, a ' + routeType.toLowerCase() + ' route could not be calculated for this destination.';
                overlay.classList.add('active');
            }
        }

        var hamburger = document.getElementById('hamburger');
        var mobileNav = document.getElementById('mobileNav');
        if (hamburger && mobileNav) {
            hamburger.addEventListener('click', function() {
                hamburger.classList.toggle('active');
                mobileNav.classList.toggle('active');
            });
            mobileNav.querySelectorAll('a').forEach(function(a) {
                a.addEventListener('click', function() { hamburger.classList.remove('active'); mobileNav.classList.remove('active'); });
            });
        }

        var comingSoonOverlay = document.getElementById('comingSoonOverlay');
        var comingSoonClose = document.getElementById('comingSoonClose');
        document.querySelectorAll('.coming-soon-trigger').forEach(function(btn) {
            btn.addEventListener('click', function(e) { e.preventDefault(); comingSoonOverlay.classList.add('active'); });
        });
        if (comingSoonClose) comingSoonClose.addEventListener('click', function() { comingSoonOverlay.classList.remove('active'); });
        if (comingSoonOverlay) comingSoonOverlay.addEventListener('click', function(e) { if (e.target === comingSoonOverlay) comingSoonOverlay.classList.remove('active'); });
        document.addEventListener('keydown', function(e) { if (e.key === 'Escape' && comingSoonOverlay) comingSoonOverlay.classList.remove('active'); });

        function highlightRouteOnMap(routeType) {
            if (!currentRoutes || currentRoutes.length === 0) return;
            routeLayers.forEach(function(layer) { layer.setStyle({ opacity: 0.2, weight: 2 }); });
            var targetIdx = currentRoutes.findIndex(function(r) { return r.route_type === routeType; });
            if (targetIdx >= 0 && routeLayers[targetIdx]) {
                routeLayers[targetIdx].setStyle({ opacity: 1, weight: 6 });
                map.fitBounds(routeLayers[targetIdx].getBounds(), { padding: [50, 50] });
            }
            selectedRouteType = routeType;
        }

        function resetRouteHighlight() {
            routeLayers.forEach(function(layer) { layer.setStyle({ opacity: 0.85, weight: 3 }); });
            if (routeLayers.length > 0) routeLayers[0].setStyle({ weight: 5 });
            selectedRouteType = null;
        }

        function updateDashboardForRoute(route) {
            if (!route) return;
            var vals = document.querySelectorAll('.safety-value');
            if (vals[0]) vals[0].textContent = route.average_risk + '/100';
            if (vals[1]) vals[1].textContent = route.risk_level;
            if (vals[2]) vals[2].textContent = 'Live';
            if (vals[3]) vals[3].textContent = route.duration_min + ' min';
            if (route.waypoints && route.waypoints.length > 0) {
                var midWp = route.waypoints[Math.floor(route.waypoints.length / 2)];
                if (midWp && midWp.reasons && midWp.reasons.length > 0) {
                    document.getElementById('live-road').textContent = midWp.reasons[0] || 'Normal';
                }
            }
        }

        function drawRoutesOnMap(routes) {
            if (!routes || routes.length === 0) return;
            routeLayers.forEach(function(layer) { map.removeLayer(layer); });
            routeLayers = [];
            var colorMap = { 'safest': '#2BB884', 'balanced': '#3479EF', 'fastest': '#FF4500', 'alternative': '#CBD5E1' };
            routes.forEach(function(route, i) {
                if (!route.geometry) return;
                var color = colorMap[route.route_type] || '#CBD5E1';
                var weight = i === 0 ? 5 : 3;
                var coords = route.geometry.map(function(p) { return [p[0], p[1]]; });
                var polyline = L.polyline(coords, { color: color, weight: weight, opacity: 0.85 }).addTo(map);
                routeLayers.push(polyline);
                if (i === 0) map.fitBounds(polyline.getBounds(), { padding: [20, 20] });
            });
        }

        function updateRouteCards(routes) {
            if (!routes) return;
            var typeMap = { '.safest-card': 'safest', '.balanced-card': 'balanced', '.fastest-card': 'fastest' };
            Object.keys(typeMap).forEach(function(selector) {
                var card = document.querySelector(selector);
                if (!card) return;
                var routeType = typeMap[selector];
                var route = routes.find(function(r) { return r.route_type === routeType; });
                if (route) {
                    card.classList.remove('unavailable', 'selected');
                    card.style.opacity = '';
                    card.style.pointerEvents = '';
                    var statVals = card.querySelectorAll('.stat-value');
                    if (statVals[0]) statVals[0].textContent = route.distance_km + ' km';
                    if (statVals[1]) statVals[1].textContent = route.duration_min + ' min';
                    var score = card.querySelector('.risk-score-value');
                    if (score) score.textContent = route.average_risk;
                    var riskTag = card.querySelector('.risk-tag');
                    if (riskTag) riskTag.textContent = route.risk_level;
                } else {
                    card.classList.add('unavailable');
                    card.classList.remove('selected');
                }
            });
        }

        function updateDashboard(riskData) {
            if (!riskData || !riskData.features) return;
            document.getElementById('live-accident').textContent = riskData.features.accident_density;
            document.getElementById('live-weather').textContent = riskData.features.temperature + '\u00B0C';
            document.getElementById('live-road').textContent = riskData.risk_level || 'Normal';
            document.getElementById('live-traffic').textContent = riskData.features.is_rush_hour === 1 ? 'Rush Hour' : 'Normal Flow';
        }

        function formatDateTimeLocal(d) {
            var year = d.getFullYear();
            var month = String(d.getMonth() + 1).padStart(2, '0');
            var day = String(d.getDate()).padStart(2, '0');
            var hours = String(d.getHours()).padStart(2, '0');
            var mins = String(d.getMinutes()).padStart(2, '0');
            return year + '-' + month + '-' + day + 'T' + hours + ':' + mins;
        }
    });
