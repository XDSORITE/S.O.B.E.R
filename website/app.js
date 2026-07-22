    // =====================
    // Autocomplete Engine
    // =====================



    var API_BASE = 'https://s-o-b-e-r.onrender.com';

    function handleRouteSearch() {
    var from = window.selectedFrom;
    var to = window.selectedTo;

    if (!from || !to) {
        alert('Please select both starting location and destination.');
        return;
    }

    findRoutesBtn.disabled = true;
    findRoutesBtn.textContent = 'Analyzing Risk & Routes...';

    var requestBody = {
        origin: [from.lat, from.lon],
        destination: [to.lat, to.lon]
    };

    // STEP 1: Call /risk FIRST
    fetch(API_BASE + '/risk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
    })
    .then(function(res) {
        if (!res.ok) throw new Error('Risk API error: ' + res.status);
        return res.json();
    })
    .then(function(riskData) {
        // STEP 2: Immediately update the dashboard UI
        updateDashboardUI(riskData);

        // STEP 3: Now fetch the routes
        return fetch(API_BASE + '/routes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
        });
    })
    .then(function(res) {
        if (!res.ok) throw new Error('Routes API error: ' + res.status);
        return res.json();
    })
    .then(function(routeData) {
        // Render routes on map and cards
        updateRouteCards(routeData.routes);
        drawRoutesOnMap(routeData.routes);
    })
    .catch(function(err) {
        console.error('Error in risk/route pipeline:', err);
    })
    .finally(function() {
        findRoutesBtn.disabled = false;
        findRoutesBtn.textContent = 'Find Safe Routes';
    });
    }

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

            // Build "Current location" option if requested
            var showCurrentLocation = opts && opts.showCurrentLocation;
            var onSelect = opts && opts.onSelect;
            var map = opts && opts.map;

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
                
                // Nominatim uses road, town/village/city, state, country
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
                if (showCurrentLocation) {
                    html += renderCurrentLocation();
                }
                if (isOpen) {
                    if (items.length === 0) {
                        html += renderNoResults();
                    } else {
                        items.forEach(function(feat, i) {
                            html += renderItem(feat, i);
                        });
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
                // Nominatim returns lat/lon as strings in jsonv2, convert to numbers
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
                if (onSelect) {
                    onSelect({ lat: lat, lon: lon, label: label, properties: feat });
                }
            }

            function selectCurrentLocation() {
                input.value = 'Current location';
                close();
                if (opts && opts.onCurrentLocation) {
                    opts.onCurrentLocation();
                }
            }

            var fetchSuggestions = debounce(function(query) {
                currentQuery = query;
                if (query.length < MIN_CHARS) {
                    items = [];
                    close();
                    return;
                }

                // Show loading
                dropdown.innerHTML = (showCurrentLocation ? renderCurrentLocation() : '') + renderLoading();
                dropdown.classList.add('active');
                isOpen = true;

                var params = 'format=jsonv2&limit=' + MAX_RESULTS + '&addressdetails=1&q=' + encodeURIComponent(query);
                var url = GEOCODER + '?' + params;

                // Call Nominatim directly without corsproxy.io
                fetch(url, {
                    headers: { 'Accept': 'application/json' }
                })
                .then(function(response) {
                    if (!response.ok) {
                        throw new Error('Geocoding request failed with status ' + response.status);
                    }
                    return response.json();
                })
                .then(function(data) {
                    if (currentQuery !== query) return; // stale
                    // Filter checking for valid jsonv2 properties (lat, lon, display_name)
                    items = (data || []).filter(function(f) {
                        return f && f.lat && f.lon && f.display_name;
                    });
                    render();
                })
                .catch(function() {
                    if (currentQuery !== query) return;
                    items = [];
                    render();
                });
            }, DEBOUNCE_MS);

            // Event listeners
            input.addEventListener('input', function() {
                fetchSuggestions(this.value);
            });

            input.addEventListener('focus', function() {
                if (this.value.length >= MIN_CHARS && items.length > 0) {
                    isOpen = true;
                    render();
                }
            });

            input.addEventListener('keydown', function(e) {
                if (!isOpen) return;

                var totalItems = items.length + (showCurrentLocation ? 1 : 0);

                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    highlightIdx = Math.min(highlightIdx + 1, totalItems - 1);
                    updateHighlight();
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    highlightIdx = Math.max(highlightIdx - 1, 0);
                    updateHighlight();
                } else if (e.key === 'Enter') {
                    e.preventDefault();
                    if (highlightIdx === 0 && showCurrentLocation) {
                        selectCurrentLocation();
                    } else if (highlightIdx >= 0) {
                        var itemIdx = showCurrentLocation ? highlightIdx - 1 : highlightIdx;
                        selectItem(itemIdx);
                    }
                } else if (e.key === 'Escape') {
                    e.preventDefault();
                    close();
                }
            });

            // Close on outside click
            document.addEventListener('mousedown', function(e) {
                if (!input.contains(e.target) && !dropdown.contains(e.target)) {
                    close();
                }
            });

            // Event delegation for dropdown items
            dropdown.addEventListener('mousedown', function(e) {
                var target = e.target.closest('.autocomplete-item, .autocomplete-current-location');
                if (!target) return;
                e.preventDefault();
                if (target.dataset.type === 'current-location') {
                    selectCurrentLocation();
                } else {
                    selectItem(parseInt(target.dataset.index));
                }
            });

            return {
                close: close,
                setValue: function(v) { input.value = v; },
                getValue: function() { return input.value; }
            };
        }

        return { create: create };
    })();


    // =====================
    // App Initialization
    // =====================
    document.addEventListener('DOMContentLoaded', function() {
        var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        // --- Toast notification system (replaces alert()) ---
        var toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container';
            toastContainer.setAttribute('aria-live', 'polite');
            toastContainer.setAttribute('role', 'status');
            document.body.appendChild(toastContainer);
        }

        function showToast(message, duration) {
            var toast = document.createElement('div');
            toast.className = 'toast-notification';
            toast.textContent = message;
            toastContainer.appendChild(toast);
            setTimeout(function() {
                toast.classList.add('toast-fade-out');
                setTimeout(function() {
                    if (toast.parentNode) {
                        toast.parentNode.removeChild(toast);
                    }
                }, prefersReducedMotion ? 0 : 300);
            }, duration || 3000);
        }

        var routeOriginalText = '';
        var originalFromPlaceholder = '';
        var findRoutesBtn = document.getElementById('findRoutesBtn');

        // Initialize Leaflet map
        var map = L.map('map', {
            center: [28.6139, 77.2090],
            zoom: 13,
            zoomControl: true
        });

        L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(map);

        map.zoomControl.setPosition('topleft');

        // Current location state
        var currentLat = null;
        var currentLon = null;
        var currentMarker = null;
        var accuracyCircle = null;

        // Set departure time to now
        var departureTimeInput = document.getElementById('departureTime');
        departureTimeInput.value = formatDateTimeLocal(new Date());

        // Now button
        document.getElementById('nowBtn').addEventListener('click', function() {
            departureTimeInput.value = formatDateTimeLocal(new Date());
        });

        // Autocomplete: From (with Current location option)
        var fromAC = Autocomplete.create('fromInput', 'fromDropdown', {
            showCurrentLocation: true,
            map: map,
            onSelect: function(result) {
                window.selectedFrom = { lat: result.lat, lon: result.lon };
                map.setView([result.lat, result.lon], 15);
            },
            onCurrentLocation: function() {
                getCurrentLocation();
            }
        });

        var toAC = Autocomplete.create('toInput', 'toDropdown', {
            showCurrentLocation: true,
            map: map,
            onSelect: function(result) {
                window.selectedTo = { lat: result.lat, lon: result.lon };
                map.setView([result.lat, result.lon], 15);
            },
            onCurrentLocation: function() {
                getCurrentLocation();
            }
        });

        // GPS Button
        document.getElementById('gpsBtn').addEventListener('click', function() {
            getCurrentLocation();
        });

        function getCurrentLocation() {
            if (!navigator.geolocation) {
                showToast('Geolocation is not supported by your browser.');
                return;
            }

            // Show loading state
            var fromInput = document.getElementById('fromInput');
            originalFromPlaceholder = fromInput.placeholder;
            fromInput.value = 'Getting location...';
            fromInput.disabled = true;

            navigator.geolocation.getCurrentPosition(
                function(pos) {
                    currentLat = pos.coords.latitude;
                    currentLon = pos.coords.longitude;
                    fromInput.value = 'Current location';
                    fromInput.disabled = false;

                    window.selectedFrom = { lat: currentLat, lon: currentLon };

                    // Center map and add/update marker
                    map.setView([currentLat, currentLon], 15);
                    if (currentMarker) {
                        currentMarker.setLatLng([currentLat, currentLon]);
                    } else {
                        currentMarker = L.circleMarker([currentLat, currentLon], {
                            radius: 8,
                            fillColor: '#4285F4',
                            fillOpacity: 1,
                            color: '#fff',
                            weight: 3,
                            opacity: 1
                        }).addTo(map);
                    }

                    // Accuracy circle - remove old one before creating new
                    if (accuracyCircle) map.removeLayer(accuracyCircle);
                    accuracyCircle = L.circleMarker([currentLat, currentLon], {
                        radius: pos.coords.accuracy || 50,
                        fillColor: '#4285F4',
                        fillOpacity: 0.1,
                        color: '#4285F4',
                        weight: 1,
                        opacity: 0.3
                    }).addTo(map);
                },
                function(err) {
                    fromInput.value = '';
                    fromInput.disabled = false;
                    fromInput.placeholder = originalFromPlaceholder;
                    if (err.code === 1) {
                        showToast('Location access denied. Please enable location permissions.');
                    } else {
                        showToast('Unable to get your location. Please enter it manually.');
                    }
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
            );
        }

        // Auto-detect location on load
        if (navigator.geolocation) {
            navigator.permissions.query({ name: 'geolocation' }).then(function(status) {
                if (status.state === 'granted') {
                    getCurrentLocation();
                }
            }).catch(function() {
                // permissions API not supported, don't auto-detect
            });
        }

        // Find Safe Routes
        findRoutesBtn.addEventListener('click', function(e) {
            if (e && typeof e.preventDefault === 'function') {
                e.preventDefault();
            }

            var from = document.getElementById('fromInput').value;
            var to = document.getElementById('toInput').value;
            
            if (!from.trim() || !to.trim()) {
                showToast('Please enter both starting point and destination.');
                return;
            }
            
            if (!window.selectedFrom || !window.selectedTo) {
                showToast('Please select locations from the dropdown suggestions.');
                return;
            }

            routeOriginalText = findRoutesBtn.textContent;
            findRoutesBtn.disabled = true;
            findRoutesBtn.textContent = 'Analyzing Risk & Routes...';

            // Extract starting location coordinates
            var slat = window.selectedFrom.lat;
            var slon = window.selectedFrom.lon;

            // STEP 1: Call /risk with slat & slon only
            var riskUrl = API_BASE + '/risk?lat=' + slat + '&lon=' + slon;

            fetch(riskUrl)
            .then(function(res) {
                if (!res.ok) throw new Error('Risk API error: ' + res.status);
                return res.json();
            })
            .then(function(riskData) {
                // STEP 2: Update Dashboard with local risk assessment
                updateDashboard(riskData);

                // STEP 3: Call /safe_route with both origin & destination
                var safeRouteUrl = API_BASE + '/safe_route' +
                    '?olat=' + slat +
                    '&olon=' + slon +
                    '&dlat=' + window.selectedTo.lat +
                    '&dlon=' + window.selectedTo.lon;

                return fetch(safeRouteUrl);
            })
            .then(function(res) {
                if (!res.ok) throw new Error('Safe Route API error: ' + res.status);
                return res.json();
            })
            .then(function(routeData) {
                // STEP 4: Render routes on map and cards
                if (routeData && routeData.routes) {
                    updateRouteCards(routeData.routes);
                    drawRoutesOnMap(routeData.routes);
                }
            })
            .catch(function(err) {
                console.error('Error in risk/route pipeline:', err);
                showToast('Could not fetch safety route details. Please try again.');
            })
            .finally(function() {
                findRoutesBtn.disabled = false;
                findRoutesBtn.textContent = routeOriginalText || 'Find Safe Routes';
            });
        });

        // Select Route - click and keyboard on card
        var routeCards = document.querySelectorAll('.route-card-inner');
        routeCards.forEach(function(card) {
            card.addEventListener('click', function() {
                selectRoute(this);
            });
            card.setAttribute('tabindex', '0');
            card.setAttribute('role', 'button');
            card.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    selectRoute.call(this);
                }
            });
        });

        // Hamburger menu
        var hamburger = document.getElementById('hamburger');
        var mobileNav = document.getElementById('mobileNav');
        if (hamburger && mobileNav) {
            hamburger.addEventListener('click', function() {
                hamburger.classList.toggle('active');
                mobileNav.classList.toggle('active');
            });
            mobileNav.querySelectorAll('a').forEach(function(a) {
                a.addEventListener('click', function() {
                    hamburger.classList.remove('active');
                    mobileNav.classList.remove('active');
                });
            });
        }

        // --- Coming Soon modal (moved from inline script) ---
        function closeComingSoon() {
            var overlay = document.getElementById('comingSoonOverlay');
            if (overlay) overlay.classList.remove('active');
        }

        var comingSoonOverlay = document.getElementById('comingSoonOverlay');
        var comingSoonClose = document.getElementById('comingSoonClose');
        document.querySelectorAll('.coming-soon-trigger').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                comingSoonOverlay.classList.add('active');
            });
        });
        if (comingSoonClose) {
            comingSoonClose.addEventListener('click', function() {
                closeComingSoon();
            });
        }
        if (comingSoonOverlay) {
            comingSoonOverlay.addEventListener('click', function(e) {
                if (e.target === comingSoonOverlay) closeComingSoon();
            });
        }
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') closeComingSoon();
        });

        // --- Route selection logic ---
        function selectRoute(card) {
            if (!card) return;

            // 🛑 1. GUARD CLAUSE: If card is unavailable, trigger popup & exit immediately
            if (card.classList.contains('unavailable')) {
                showUnavailablePopup(card);
                return; // Stops selection completely!
            }

            var allCards = document.querySelectorAll('.route-card-inner');

            // 2. Deselect if clicking an already selected card
            if (card.classList.contains('selected')) {
                card.classList.remove('selected');
                allCards.forEach(function(c) {
                    if (!c.classList.contains('unavailable')) {
                        c.style.opacity = '';
                        c.style.pointerEvents = '';
                    }
                });
                return;
            }

            // 3. Dim other available cards & select clicked card
            allCards.forEach(function(c) {
                c.classList.remove('selected');
                // Only dim cards that are available
                if (!c.classList.contains('unavailable')) {
                    c.style.opacity = '0.4';
                }
            });

            card.classList.add('selected');
            card.style.opacity = '1';
            card.style.pointerEvents = 'auto';

            if (window.innerWidth <= 768) {
                var isReduced = typeof prefersReducedMotion !== 'undefined' ? prefersReducedMotion : false;
                card.scrollIntoView({ behavior: isReduced ? 'auto' : 'smooth', block: 'center' });
            }
        }

        // --- Helper to open the Unavailable Popup Modal ---
        function showUnavailablePopup(card) {
            var routeType = 'Safest';
            if (card.classList.contains('balanced-card')) routeType = 'Balanced';
            if (card.classList.contains('fastest-card')) routeType = 'Fastest';

            var overlay = document.querySelector('.coming-soon-overlay');
            if (overlay) {
                var title = overlay.querySelector('.coming-soon-title');
                var text = overlay.querySelector('.coming-soon-text');

                if (title) title.textContent = routeType + ' Route Unavailable';
                if (text) text.textContent = 'Sorry, a ' + routeType.toLowerCase() + ' route could not be calculated for this destination. Please select an available route.';

                overlay.classList.add('active');
            }
        }

        // --- Date formatting ---
        function formatDateTimeLocal(d) {
            var year = d.getFullYear();
            var month = String(d.getMonth() + 1).padStart(2, '0');
            var day = String(d.getDate()).padStart(2, '0');
            var hours = String(d.getHours()).padStart(2, '0');
            var mins = String(d.getMinutes()).padStart(2, '0');
            return year + '-' + month + '-' + day + 'T' + hours + ':' + mins;
        }

        // --- Route simulation ---
        function simulateRoutes() {
            var routes = [
                { type: 'safest', distance: '12.3', time: '28', risk: '2.1' },
                { type: 'balanced', distance: '10.8', time: '22', risk: '5.4' },
                { type: 'fastest', distance: '9.2', time: '18', risk: '8.7' }
            ];

            var safetyData = ['Low', 'Clear', 'Good', 'Moderate'];

            var allCards = document.querySelectorAll('.route-card-inner');
            allCards.forEach(function(c) {
                c.style.opacity = '0';
                c.style.transform = 'translateY(20px)';
            });

            routes.forEach(function(route, i) {
                setTimeout(function() {
                    var card = document.querySelector('.' + route.type + '-card');
                    if (!card) return;
                    var transitionDuration = prefersReducedMotion ? 0 : 400;
                    card.style.transition = 'opacity ' + transitionDuration + 'ms, transform ' + transitionDuration + 'ms';
                    card.style.opacity = '0.7';
                    card.style.transform = 'translateY(0)';

                    var statVals = card.querySelectorAll('.stat-value');
                    if (statVals[0]) statVals[0].textContent = route.distance + ' km';
                    if (statVals[1]) statVals[1].textContent = route.time + ' min';
                    var score = card.querySelector('.risk-score-value');
                    if (score) {
                        score.textContent = route.risk;
                        if (!prefersReducedMotion) {
                            score.style.animation = 'none';
                            score.offsetHeight;
                            score.style.animation = 'scoreCount 0.5s ease forwards';
                        }
                    }
                }, prefersReducedMotion ? 0 : i * 200);
            });

            setTimeout(function() {
                var vals = document.querySelectorAll('.safety-value');
                vals.forEach(function(v, i) {
                    setTimeout(function() {
                        v.style.transition = prefersReducedMotion ? 'none' : 'opacity 0.3s';
                        v.style.opacity = '0';
                        setTimeout(function() {
                            v.textContent = safetyData[i];
                            v.style.opacity = '1';
                        }, prefersReducedMotion ? 0 : 150);
                    }, prefersReducedMotion ? 0 : i * 100);
                });
            }, prefersReducedMotion ? 0 : 800);

            findRoutesBtn.disabled = false;
            findRoutesBtn.textContent = routeOriginalText || 'Find Safe Routes';
        }


        // List of all expected route types
        const routeTypes = ['safest', 'balanced', 'fastest'];

        function updateRouteCards(routes) {
            if (!routes) return;

            var selectors = ['.safest-card', '.balanced-card', '.fastest-card'];

            selectors.forEach(function(selector, i) {
                var card = document.querySelector(selector);
                if (!card) return;

                var route = routes[i]; // Undefined if route missing

                if (route) {
                    // --- ROUTE AVAILABLE ---
                    card.classList.remove('unavailable');
                    
                    // Populate stats
                    var statVals = card.querySelectorAll('.stat-value');
                    if (statVals[0]) statVals[0].textContent = route.distance_km + ' km';
                    if (statVals[1]) statVals[1].textContent = route.duration_min + ' min';
                    
                    var score = card.querySelector('.risk-score-value');
                    if (score) score.textContent = route.average_risk;
                } else {
                    // --- ROUTE UNAVAILABLE ---
                    card.classList.add('unavailable');
                    card.classList.remove('selected');
                }
            });
        }

        function updateSafetyPanel(route) {
            var vals = document.querySelectorAll('.safety-value');
            if (vals[0]) vals[0].textContent = route.average_risk + '/100';
            if (vals[1]) vals[1].textContent = route.risk_level;
            if (vals[2]) vals[2].textContent = 'Live';
            if (vals[3]) vals[3].textContent = route.duration_min + ' min';
        }

        // Add a variable at the top of DOMContentLoaded:
        var routeLayers = [];

        function drawRoutesOnMap(routes) {
            if (!routes || routes.length === 0) return;

            // Clear previous route polylines
            routeLayers.forEach(function(layer) {
                map.removeLayer(layer);
            });
            routeLayers = [];

            var colors = ['#2BB884', '#3479EF', '#FF4500'];

            routes.forEach(function(route, i) {
                if (!route.geometry) return;
                var color = colors[i] || '#CBD5E1';
                var weight = i === 0 ? 5 : 3;
                var coords = route.geometry.map(function(p) { return [p[0], p[1]]; });
                
                var polyline = L.polyline(coords, { color: color, weight: weight, opacity: 0.85 }).addTo(map);
                routeLayers.push(polyline); // Track for deletion
                
                if (i === 0) {
                    map.fitBounds(polyline.getBounds(), { padding: [20, 20] });
                }
            });
        }

        function updateDashboard(riskData) {
            if (!riskData || !riskData.features) return;

            const accidentDensity = riskData.features.accident_density;
            const weatherText = riskData.features.temperature + '°C';
            const roadRiskLevel = riskData.risk_level || 'Normal';
            const trafficText = riskData.features.is_rush_hour === 1 ? 'Rush Hour' : 'Normal Flow';

            document.getElementById('live-accident').textContent = accidentDensity;
            document.getElementById('live-weather').textContent = weatherText;
            document.getElementById('live-road').textContent = roadRiskLevel;
            document.getElementById('live-traffic').textContent = trafficText;
        }
        
    });
