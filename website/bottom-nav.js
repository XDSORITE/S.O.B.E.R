// =====================
// Bottom Navigation Bar
// =====================
document.addEventListener("DOMContentLoaded", function () {
	var bottomNav = document.getElementById("bottomNav");
	if (!bottomNav) return;

	var mql = window.matchMedia("(max-width: 768px)");
	var header = document.querySelector(".header");
	var navItems = bottomNav.querySelectorAll(".bottom-nav-item");
	var sections = [];
	var lastScrollY = 0;
	var scrollDirection = "up";
	var comingSoonOverlay = document.getElementById("comingSoonOverlay");

	// Collect section elements from nav items
	navItems.forEach(function (item) {
		var sectionId = item.getAttribute("data-section");
		if (sectionId) {
			var section = document.getElementById(sectionId);
			if (section) {
				sections.push({ id: sectionId, el: section, navItem: item });
			}
		}
	});

	// ---- 1. Active state tracking ----
	function setActive(sectionId) {
		navItems.forEach(function (item) {
			if (item.getAttribute("data-section") === sectionId) {
				item.classList.add("active");
			} else {
				item.classList.remove("active");
			}
		});
	}

	// ---- 2. Click handler for bottom nav items ----
	navItems.forEach(function (item) {
		item.addEventListener("click", function (e) {
			var sectionId = this.getAttribute("data-section");

			// Coming-soon items: show modal instead of navigating
			if (this.classList.contains("coming-soon-trigger")) {
				e.preventDefault();
				if (comingSoonOverlay) {
					comingSoonOverlay.classList.add("active");
				}
				return;
			}

			// If section doesn't exist or is hidden, default to coming soon
			var target = document.getElementById(sectionId);
			if (target && target.style.display === "none") {
				e.preventDefault();
				if (comingSoonOverlay) {
					comingSoonOverlay.classList.add("active");
				}
				return;
			}

			// Update active state
			setActive(sectionId);

			// Scroll to section
			if (target) {
				e.preventDefault();
				target.scrollIntoView({ behavior: "smooth", block: "start" });
			}
		});
	});

	// ---- 3. Scroll spy using IntersectionObserver ----
	var observerOptions = {
		root: null,
		rootMargin: "-20% 0px -60% 0px",
		threshold: 0,
	};

	var observer = new IntersectionObserver(function (entries) {
		// Find the most visible entry
		var visible = entries.filter(function (entry) {
			return entry.isIntersecting;
		});

		if (visible.length > 0) {
			// Use the first intersecting entry
			var sectionId = visible[0].target.getAttribute("id");
			setActive(sectionId);
		}
	}, observerOptions);

	sections.forEach(function (s) {
		observer.observe(s.el);
	});

	// ---- 4. Hide on desktop ----
	function handleViewportChange(e) {
		if (e.matches) {
			// Mobile: show bottom nav, enable scroll behavior
			bottomNav.style.display = "";
			enableScrollBehavior();
		} else {
			// Desktop: hide bottom nav, disable scroll behavior, reset header
			bottomNav.style.display = "none";
			disableScrollBehavior();
			if (header) {
				header.style.transform = "";
				header.style.transition = "";
			}
		}
	}

	// ---- 5. Sync with desktop nav ----
	function syncDesktopNav() {
		var desktopLinks = document.querySelectorAll(".nav-links .nav-link");
		desktopLinks.forEach(function (link) {
			link.addEventListener("click", function () {
				var href = this.getAttribute("href");
				if (href && href.charAt(0) === "#") {
					var sectionId = href.substring(1);
					setActive(sectionId);
				}
			});
		});
	}

	// ---- 6. Hide header on scroll down, show on scroll up (mobile only) ----
	function enableScrollBehavior() {
		if (!header) return;

		// Add transition for smooth hide/show
		header.style.transition = "transform 0.3s ease";

		window.addEventListener("scroll", onScroll, { passive: true });
	}

	function disableScrollBehavior() {
		window.removeEventListener("scroll", onScroll);
	}

	function onScroll() {
		if (!mql.matches) return;

		var currentScrollY = window.pageYOffset || document.documentElement.scrollTop;

		// Determine scroll direction
		if (currentScrollY > lastScrollY && currentScrollY > 80) {
			// Scrolling down and past threshold
			scrollDirection = "down";
		} else if (currentScrollY < lastScrollY) {
			// Scrolling up
			scrollDirection = "up";
		}

		// Toggle header visibility
		if (header) {
			if (scrollDirection === "down" && currentScrollY > 80) {
				header.style.transform = "translateY(-100%)";
			} else {
				header.style.transform = "";
			}
		}

		lastScrollY = currentScrollY;
	}

	// Initialize
	handleViewportChange(mql);
	mql.addEventListener("change", handleViewportChange);
	syncDesktopNav();
});
