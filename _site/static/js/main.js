/* ADHAYAN — lightweight progressive enhancements (no framework, no build step). */
(function () {
  "use strict";

  /* ------------------------------------------------------------ mobile nav */
  var toggle = document.getElementById("nav-toggle");
  var menu = document.getElementById("mobile-nav");
  if (toggle && menu) {
    toggle.addEventListener("click", function () {
      var open = menu.classList.toggle("hidden") === false;
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });
  }

  /* --------------------------------------------------------- scroll reveal */
  var revealables = document.querySelectorAll(".reveal");
  if (revealables.length) {
    if ("IntersectionObserver" in window) {
      var observer = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              entry.target.classList.add("is-visible");
              observer.unobserve(entry.target);
            }
          });
        },
        { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
      );
      revealables.forEach(function (node, index) {
        node.style.transitionDelay = Math.min(index % 6, 5) * 60 + "ms";
        observer.observe(node);
      });
    } else {
      revealables.forEach(function (node) {
        node.classList.add("is-visible");
      });
    }
  }

  /* --------------------------------------------------- pointer-follow glow */
  document.querySelectorAll(".card-glow").forEach(function (card) {
    card.addEventListener("pointermove", function (event) {
      var rect = card.getBoundingClientRect();
      card.style.setProperty("--mx", event.clientX - rect.left + "px");
      card.style.setProperty("--my", event.clientY - rect.top + "px");
    });
  });

  /* ---------------------------------------------------- code block controls */
  document.querySelectorAll(".prose-adhayan pre").forEach(function (pre) {
    var wrapper = document.createElement("div");
    wrapper.className = "relative";
    pre.parentNode.insertBefore(wrapper, pre);
    wrapper.appendChild(pre);

    var button = document.createElement("button");
    button.type = "button";
    button.className =
      "absolute right-2 top-2 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-[11px] uppercase tracking-wider text-mist-soft opacity-0 transition hover:border-accent/40 hover:text-mist-bright";
    button.textContent = "Copy";
    wrapper.appendChild(button);
    wrapper.addEventListener("pointerenter", function () {
      button.style.opacity = "1";
    });
    wrapper.addEventListener("pointerleave", function () {
      button.style.opacity = "0";
    });
    button.addEventListener("click", function () {
      var code = pre.querySelector("code");
      var text = (code || pre).innerText;
      if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function () {
          button.textContent = "Copied";
          setTimeout(function () {
            button.textContent = "Copy";
          }, 1600);
        });
      }
    });
  });

  /* ------------------------------------------ admin: markdown live preview */
  var editor = document.getElementById("md-content");
  var preview = document.getElementById("md-preview");
  var previewButton = document.getElementById("md-preview-toggle");
  if (editor && preview && previewButton) {
    var pending = null;
    var render = function () {
      if (pending) window.clearTimeout(pending);
      pending = window.setTimeout(function () {
        fetch("/admin/markdown-preview", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')
              ? document.querySelector('meta[name="csrf-token"]').content
              : "",
          },
          body: JSON.stringify({ text: editor.value }),
        })
          .then(function (response) {
            return response.json();
          })
          .then(function (data) {
            preview.innerHTML = data.html || "<p class='text-mist-soft'>Nothing to preview.</p>";
          })
          .catch(function () {
            preview.innerHTML = "<p class='text-mist-soft'>Preview unavailable.</p>";
          });
      }, 350);
    };

    previewButton.addEventListener("click", function () {
      var showing = preview.classList.toggle("hidden") === false;
      editor.classList.toggle("hidden", showing);
      previewButton.textContent = showing ? "Write" : "Preview";
      if (showing) render();
    });
    editor.addEventListener("input", function () {
      if (!preview.classList.contains("hidden")) render();
    });
  }

  /* ------------------------------------------ admin: image upload previews */
  document.querySelectorAll("input[type=file][data-preview]").forEach(function (input) {
    input.addEventListener("change", function () {
      var target = document.querySelector(input.getAttribute("data-preview"));
      if (!target) return;
      var file = input.files && input.files[0];
      if (!file) return;
      target.src = URL.createObjectURL(file);
      target.classList.remove("hidden");
    });
  });

  /* ------------------------------------------------------ background video */
  var bgVideo = document.querySelector(".bg-video");
  if (bgVideo) {
    var motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    var syncPlayback = function () {
      if (motionQuery.matches) {
        bgVideo.pause();
      } else if (!document.hidden) {
        var attempt = bgVideo.play();
        if (attempt && attempt.catch) attempt.catch(function () {});
      }
    };
    syncPlayback();
    if (motionQuery.addEventListener) {
      motionQuery.addEventListener("change", syncPlayback);
    } else if (motionQuery.addListener) {
      motionQuery.addListener(syncPlayback);
    }
    document.addEventListener("visibilitychange", syncPlayback);
  }
})();
