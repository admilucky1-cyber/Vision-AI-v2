(function () {
  function el(tag, props, children) {
    var node = document.createElement(tag);
    props = props || {};
    Object.keys(props).forEach(function (k) {
      if (k === "className") node.className = props[k];
      else if (k === "text") node.textContent = props[k];
      else if (k.slice(0, 2) === "on" && typeof props[k] === "function") node.addEventListener(k.slice(2).toLowerCase(), props[k]);
      else if (k !== "html") node.setAttribute(k, props[k]);
    });
    (children || []).forEach(function (c) {
      if (c == null) return;
      node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return node;
  }

  function token() {
    return localStorage.getItem("vision_ai_access_token") || localStorage.getItem("vision_ai_access") || "";
  }
  async function api(path, opts) {
    opts = opts || {};
    const headers = Object.assign({ Accept: "application/json" }, opts.headers || {});
    if (token()) headers.Authorization = "Bearer " + token();
    if (opts.body && typeof opts.body === "object" && !(opts.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(opts.body);
    }
    const res = await fetch(path, Object.assign({}, opts, { headers }));
    let data = {};
    try { data = await res.json(); } catch (e) {}
    if (!res.ok) {
      const d = data.detail;
      const msg = typeof d === "string" ? d : (d && d.message) || data.error || res.statusText;
      throw new Error(msg || ("HTTP " + res.status));
    }
    return data;
  }
  function $(id) { return document.getElementById(id); }
  function show(el, text, ok) {
    el.textContent = text || "";
    el.className = "msg " + (ok ? "ok" : "err");
  }

  document.querySelectorAll(".tabs button").forEach(function (btn) {
    btn.onclick = function () {
      document.querySelectorAll(".tabs button").forEach(function (b) { b.classList.remove("active"); });
      document.querySelectorAll(".panel").forEach(function (p) { p.classList.remove("active"); });
      btn.classList.add("active");
      var p = $("panel-" + btn.getAttribute("data-tab"));
      if (p) p.classList.add("active");
      if (btn.getAttribute("data-tab") === "jobs") loadJobs();
      if (btn.getAttribute("data-tab") === "models") loadModels();
    };
  });

  async function loadModels() {
    try {
      const data = await api("/api/studio/models");
      const models = data.models || [];
      const imgSel = $("imgModel");
      const vidSel = $("vidModel");
      const trainSel = $("trainBase");
      const grid = $("modelGrid");
      [imgSel, vidSel, trainSel].forEach(function (s) { if (s) s.innerHTML = ""; });
      if (grid) grid.innerHTML = "";
      models.forEach(function (m) {
        const opt = document.createElement("option");
        opt.value = m.id;
        opt.textContent = m.name + " (" + m.type + ")";
        if (m.type === "image" && imgSel) imgSel.appendChild(opt.cloneNode(true));
        if (m.type === "video" && vidSel) vidSel.appendChild(opt.cloneNode(true));
        if (m.type === "image" && trainSel) trainSel.appendChild(opt.cloneNode(true));
        if (grid) {
          const card = el("div", { className: "card" }, [
            el("strong", { text: m.name || m.id }),
            document.createElement("br"),
            document.createTextNode((m.type || "") + " · VRAM " + (m.vram_gb != null ? m.vram_gb : "?") + "GB"),
            document.createElement("br"),
            document.createTextNode(m.hf_id || m.source || "")
          ]);
          grid.appendChild(card);
        }
      });
      const loras = await api("/api/studio/loras");
      const ls = $("imgLora");
      if (ls) {
        ls.innerHTML = '<option value="">None</option>';
        (loras.loras || []).forEach(function (l) {
          const o = document.createElement("option");
          o.value = l.id;
          o.textContent = l.name || l.id;
          ls.appendChild(o);
        });
      }
    } catch (e) {
      if ($("modelGrid")) $("modelGrid").innerHTML = "<div class='card'>" + e.message + "</div>";
    }
  }

  async function loadJobs() {
    try {
      const data = await api("/api/studio/jobs");
      const grid = $("jobGrid");
      if (!grid) return;
      grid.innerHTML = "";
      (data.jobs || []).forEach(function (j) {
        const card = el("div", { className: "card" }, [
          el("strong", { text: (j.type || "job") }),
          document.createTextNode(" · " + (j.status || "")),
          document.createElement("br"),
          document.createTextNode(String(j.prompt || j.dataset_id || j.id || "").slice(0, 80))
        ]);
        grid.appendChild(card);
      });
      if (!(data.jobs || []).length) grid.innerHTML = "<div class='card'>No jobs yet</div>";
    } catch (e) {
      if ($("jobGrid")) $("jobGrid").innerHTML = "<div class='card'>" + e.message + " — sign in required</div>";
    }
  }

  $("imgGen").onclick = async function () {
    show($("imgMsg"), "Generating…", true);
    $("imgPreview").innerHTML = "";
    try {
      const data = await api("/api/studio/generate", {
        method: "POST",
        body: {
          prompt: $("imgPrompt").value,
          negative_prompt: ($("imgNeg") && $("imgNeg").value) || "",
          model_id: $("imgModel").value || "sdxl-turbo",
          lora_id: $("imgLora").value || null
        }
      });
      show($("imgMsg"), "OK · " + (data.provider || "") + " · job " + (data.job_id || ""), true);
      const imgs = data.images || [];
      imgs.forEach(function (im) {
        const url = im.url || (im.data && im.data.indexOf("data:") === 0 ? im.data : (im.data ? "data:image/png;base64," + im.data : null));
        if (url) {
          const img = document.createElement("img");
          img.src = url;
          $("imgPreview").appendChild(img);
        }
      });
    } catch (e) {
      show($("imgMsg"), e.message, false);
    }
  };

  $("vidGen").onclick = async function () {
    try {
      const data = await api("/api/studio/video", {
        method: "POST",
        body: { prompt: $("vidPrompt").value, mode: $("vidMode").value || "i2v", model_id: $("vidModel").value || "svd-xt" }
      });
      show($("vidMsg"), "Queued " + (data.job && data.job.id) + " — " + (data.note || ""), true);
    } catch (e) {
      show($("vidMsg"), e.message, false);
    }
  };

  $("trainStart").onclick = async function () {
    try {
      const data = await api("/api/studio/train", {
        method: "POST",
        body: {
          dataset_id: $("trainDs").value,
          base_model: $("trainBase").value || "flux-schnell",
          rank: Number($("trainRank").value || 16),
          epochs: Number($("trainEpochs").value || 10)
        }
      });
      show($("trainMsg"), "Queued " + (data.job && data.job.id), true);
    } catch (e) {
      show($("trainMsg"), e.message, false);
    }
  };

  $("dsReg").onclick = async function () {
    try {
      const data = await api("/api/studio/datasets", {
        method: "POST",
        body: { name: $("dsName").value, drive_path: $("dsPath").value }
      });
      show($("dsMsg"), "Registered " + (data.dataset && data.dataset.id), true);
      if (data.dataset && data.dataset.id) $("trainDs").value = data.dataset.id;
    } catch (e) {
      show($("dsMsg"), e.message, false);
    }
  };

  loadModels();
})();
