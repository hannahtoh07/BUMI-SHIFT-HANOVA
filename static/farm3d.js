
/*
 BUMI SHIFT 7.0
 Interactive 3D Farming SHIFT Planner
 HANOVA | Sarawak, Malaysia

 Features:
 - 11 recognizable crop models
 - Baseline versus proposed SHIFT
 - Rotation stage visualization
 - Paddy, raised beds, upland rows and orchards
 - Farmer-reported drainage scenarios
 - Optional soil-cover management
 - Clickable field-management explanations
 - NASA rainfall evidence integration
 - Orbit, zoom and camera reset

 This is an illustrative field-management planner.
 It does not simulate crop growth or soil hydrology.

 Compatible with the existing index.html:
 BUMIFarm3D.showCrop(id)
 BUMIFarm3D.resize()
 BUMIFarm3D.resetCamera()
*/

import * as THREE from "three";
import { OrbitControls } from
  "three/addons/controls/OrbitControls.js";

const host = document.getElementById("farm3d");

if (host) {
  initializeFarm(host);
}

function initializeFarm(host) {

  // ==========================================
  // 1. CROP INFORMATION
  // ==========================================

  const CROPS = {
    rice: {
      name: "Rice",
      system: "paddy",
      spacing: 0.65,
      duration: 4,
      explanation:
        "Paddy rice may use controlled standing water, bunds and irrigation channels."
    },
    maize: {
      name: "Maize",
      system: "rows",
      spacing: 1.2,
      duration: 4,
      explanation:
        "Maize is planted in rows. Drainage and adequate moisture during flowering are important."
    },
    mung_bean: {
      name: "Mung Bean",
      system: "rows",
      spacing: 0.85,
      duration: 3,
      explanation:
        "Mung bean is a short-duration legume. Check drainage, nodulation and residue management."
    },
    groundnut: {
      name: "Groundnut",
      system: "raised",
      spacing: 0.9,
      duration: 4,
      explanation:
        "Groundnut needs suitable soil conditions for pegging and pod development."
    },
    soybean: {
      name: "Soybean",
      system: "rows",
      spacing: 0.95,
      duration: 4,
      explanation:
        "Soybean can diversify crop families. Nitrogen benefits depend on effective nodulation."
    },
    sweet_potato: {
      name: "Sweet Potato",
      system: "raised",
      spacing: 0.95,
      duration: 4,
      explanation:
        "Raised beds can support storage-root development and drainage."
    },
    cassava: {
      name: "Cassava",
      system: "raised",
      spacing: 1.55,
      duration: 10,
      explanation:
        "Cassava requires longer field occupation, suitable drainage and soil-conservation planning."
    },
    pineapple: {
      name: "Pineapple",
      system: "raised",
      spacing: 1.25,
      duration: 16,
      explanation:
        "Pineapple requires longer-term field planning, drainage and suitable planting arrangements."
    },
    banana: {
      name: "Banana",
      system: "plantation",
      spacing: 3.0,
      duration: 12,
      explanation:
        "Banana cultivation requires drainage, wind protection and disease management."
    },
    coconut: {
      name: "Coconut",
      system: "orchard",
      spacing: 4.0,
      duration: 36,
      explanation:
        "Coconut is a long-term plantation decision requiring appropriate spacing and land commitment."
    },
    durian: {
      name: "Durian",
      system: "orchard",
      spacing: 3.8,
      duration: 60,
      explanation:
        "Durian orchard establishment requires suitable root-zone drainage, spacing and long-term management."
    }
  };

  // ==========================================
  // 2. SCENE SETUP
  // ==========================================

  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#b7dff1");
  scene.fog = new THREE.Fog("#b7dff1", 38, 90);

  const camera = new THREE.PerspectiveCamera(
    43, 1, 0.1, 150
  );

  camera.position.set(17, 17, 21);

  let renderer;

  try {
    renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false
    });
  } catch (error) {
    console.error("BUMI SHIFT WebGL:", error);
    host.textContent =
      "Interactive 3D requires WebGL support.";
    return;
  }

  renderer.setPixelRatio(
    Math.min(window.devicePixelRatio || 1, 2)
  );

  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.3;

  renderer.domElement.style.width = "100%";
  renderer.domElement.style.height = "100%";
  renderer.domElement.style.display = "block";

  host.prepend(renderer.domElement);

  const controls = new OrbitControls(
    camera, renderer.domElement
  );

  controls.enableDamping = true;
  controls.target.set(0, 0.5, 0);
  controls.minDistance = 8;
  controls.maxDistance = 48;
  controls.maxPolarAngle = Math.PI * 0.49;

  scene.add(new THREE.HemisphereLight(
    0xffffff, 0x557b58, 2.4
  ));

  const sunlight = new THREE.DirectionalLight(
    0xfff0d4, 2.8
  );

  sunlight.position.set(-9, 20, 12);
  sunlight.castShadow = true;
  sunlight.shadow.mapSize.set(1024, 1024);
  sunlight.shadow.camera.left = -22;
  sunlight.shadow.camera.right = 22;
  sunlight.shadow.camera.top = 22;
  sunlight.shadow.camera.bottom = -22;
  scene.add(sunlight);

  // ==========================================
  // 3. MATERIALS
  // ==========================================

  function material(color, options = {}) {
    return new THREE.MeshStandardMaterial({
      color,
      roughness: 0.82,
      ...options
    });
  }

  const M = {
    grass: material("#70ad65"),
    soil: material("#916344"),
    darkSoil: material("#60422e"),
    raisedSoil: material("#ad7950"),
    path: material("#e1c99c"),
    green: material("#42964b"),
    lightGreen: material("#83c966"),
    darkGreen: material("#287446"),
    bananaGreen: material("#52ae60"),
    stem: material("#7e573d"),
    paleStem: material("#8caf68"),
    yellow: material("#edca5d"),
    orange: material("#dfa147"),
    purple: material("#8854a5"),
    wall: material("#efdbbb"),
    roof: material("#ae6c48"),
    mulch: material("#c49a66"),
    water: material("#44b9df", {
      roughness: 0.2,
      transparent: true,
      opacity: 0.72
    }),
    warning: material("#f3aa38", {
      emissive: "#a35a00",
      emissiveIntensity: 0.15
    })
  };

  // ==========================================
  // 4. GEOMETRY HELPERS
  // ==========================================

  function mesh(parent, geometry, mat) {
    const object = new THREE.Mesh(geometry, mat);
    object.castShadow = true;
    object.receiveShadow = true;
    parent.add(object);
    return object;
  }

  function box(
    parent, w, h, d, mat,
    x = 0, y = 0, z = 0
  ) {
    const object = mesh(
      parent,
      new THREE.BoxGeometry(w, h, d),
      mat
    );
    object.position.set(x, y, z);
    return object;
  }

  function cylinder(
    parent, x, y, z,
    height, radius, mat
  ) {
    const object = mesh(
      parent,
      new THREE.CylinderGeometry(
        radius * 0.8, radius, height, 7
      ),
      mat
    );
    object.position.set(x, y, z);
    return object;
  }

  function sphere(
    parent, x, y, z,
    sx, sy, sz, mat
  ) {
    const object = mesh(
      parent,
      new THREE.SphereGeometry(1, 9, 7),
      mat
    );
    object.position.set(x, y, z);
    object.scale.set(sx, sy, sz);
    return object;
  }

  function leaf(
    parent, x, y, z,
    length, width, angle, mat
  ) {
    const object = sphere(
      parent, x, y, z,
      width, 0.045, length, mat
    );
    object.rotation.y = angle;
    return object;
  }

  function clearGroup(group) {
    group.traverse(object => {
      if (object.isMesh) {
        object.geometry.dispose();
      }
    });
    group.clear();
  }

  // ==========================================
  // 5. FARM LANDSCAPE
  // ==========================================

  const cropGroup = new THREE.Group();
  const managementGroup = new THREE.Group();
  const hotspotGroup = new THREE.Group();

  scene.add(cropGroup);
  scene.add(managementGroup);
  scene.add(hotspotGroup);

  box(scene, 30, 0.65, 25, M.grass, 0, -0.65, 0);
  box(scene, 22, 0.3, 18, M.soil, 0, -0.16, 0);

  // Central farm paths
  box(scene, 1.1, 0.12, 18, M.path, 0, 0.08, 0);
  box(scene, 22, 0.12, 1.0, M.path, 0, 0.08, 0);

  // Permanent drainage channels
  box(scene, 0.8, 0.08, 18, M.water, -10.1, 0.1, 0);
  box(scene, 0.8, 0.08, 18, M.water, 10.1, 0.1, 0);

  // Farmhouse
  box(scene, 2.5, 1.5, 2.2, M.wall, -12.3, 0.65, -9.5);
  const roof = box(
    scene, 3, 0.35, 2.8,
    M.roof, -12.3, 1.55, -9.5
  );
  roof.rotation.z = -0.12;

  function backgroundTree(x, z) {
    cylinder(scene, x, 0.85, z, 1.7, 0.15, M.stem);
    sphere(scene, x, 2, z, 0.8, 0.8, 0.8, M.darkGreen);
    sphere(scene, x - 0.4, 1.8, z,
      0.55, 0.5, 0.55, M.green);
  }

  for (let i = 0; i < 5; i++) {
    backgroundTree(-12, -6 + i * 3);
    backgroundTree(12, -6 + i * 3);
  }

  const plots = [
    [-5, -4.3],
    [5, -4.3],
    [-5, 4.3],
    [5, 4.3]
  ];

  // ==========================================
  // 6. ELEVEN DISTINCT CROP MODELS
  // ==========================================

  function rice(p, x, z) {
    for (let i = 0; i < 5; i++) {
      const a = i * Math.PI * 2 / 5;
      const dx = Math.cos(a);
      const dz = Math.sin(a);

      const stem = cylinder(
        p, x + dx * 0.08, 0.32,
        z + dz * 0.08, 0.62, 0.018, M.green
      );
      stem.rotation.z = dx * 0.2;

      const blade = sphere(
        p, x + dx * 0.17, 0.46,
        z + dz * 0.17,
        0.04, 0.27, 0.04, M.lightGreen
      );
      blade.rotation.z = dx * 0.45;
    }

    for (let i = 0; i < 4; i++) {
      sphere(p, x + i * 0.04 - 0.06,
        0.72, z, 0.035, 0.07, 0.035, M.yellow);
    }
  }

  function maize(p, x, z) {
    cylinder(p, x, 0.85, z, 1.7, 0.07, M.green);

    for (let i = 0; i < 7; i++) {
      const a = i * 2.4;
      const l = leaf(
        p,
        x + Math.cos(a) * 0.38,
        0.55 + i * 0.14,
        z + Math.sin(a) * 0.38,
        0.6, 0.12, a, M.darkGreen
      );
      l.rotation.z = Math.cos(a) * 0.25;
    }

    sphere(p, x + 0.16, 1.12, z,
      0.14, 0.3, 0.13, M.yellow);
  }

  function mungBean(p, x, z) {
    cylinder(p, x, 0.32, z, 0.64, 0.035, M.green);

    for (let i = 0; i < 3; i++) {
      const a = i * Math.PI * 2 / 3;
      for (let j = 0; j < 3; j++) {
        sphere(
          p,
          x + Math.cos(a) * (0.17 + j * 0.08),
          0.35 + j * 0.055,
          z + Math.sin(a) * (0.17 + j * 0.08),
          0.13, 0.045, 0.11, M.lightGreen
        );
      }
    }

    sphere(p, x + 0.18, 0.28, z,
      0.04, 0.17, 0.045, M.darkGreen);
  }

  function groundnut(p, x, z) {
    for (let i = 0; i < 6; i++) {
      const a = i * Math.PI / 3;
      cylinder(
        p, x + Math.cos(a) * 0.1,
        0.16, z + Math.sin(a) * 0.1,
        0.32, 0.025, M.green
      );

      for (let j = 0; j < 3; j++) {
        sphere(
          p,
          x + Math.cos(a) * (0.18 + j * 0.08),
          0.27,
          z + Math.sin(a) * (0.18 + j * 0.08),
          0.1, 0.035, 0.08, M.lightGreen
        );
      }
    }

    // Small illustrative exposed pods
    for (let i = 0; i < 3; i++) {
      sphere(p, x + i * 0.12 - 0.12,
        0.06, z, 0.08, 0.055, 0.06, M.orange);
    }
  }

  function soybean(p, x, z) {
    cylinder(p, x, 0.52, z, 1.04, 0.045, M.green);

    for (let i = 0; i < 5; i++) {
      const a = i * 1.25;
      for (let j = 0; j < 3; j++) {
        sphere(
          p,
          x + Math.cos(a) * (0.17 + j * 0.1),
          0.4 + j * 0.16,
          z + Math.sin(a) * (0.17 + j * 0.1),
          0.16, 0.05, 0.13, M.darkGreen
        );
      }
    }

    for (let i = 0; i < 3; i++) {
      sphere(p, x + 0.11, 0.3 + i * 0.2,
        z, 0.07, 0.13, 0.055, M.yellow);
    }
  }

  function sweetPotato(p, x, z) {
    for (let i = 0; i < 7; i++) {
      const a = i * Math.PI * 2 / 7;

      for (let j = 1; j <= 3; j++) {
        sphere(
          p,
          x + Math.cos(a) * j * 0.15,
          0.13,
          z + Math.sin(a) * j * 0.15,
          0.16, 0.035, 0.13, M.green
        );
      }
    }

    sphere(p, x + 0.15, 0.18, z,
      0.07, 0.04, 0.07, M.purple);
  }

  function cassava(p, x, z) {
    cylinder(p, x, 0.8, z, 1.6, 0.065, M.stem);

    for (let i = 0; i < 8; i++) {
      const a = i * Math.PI / 4;

      for (let j = 1; j <= 5; j++) {
        const l = sphere(
          p,
          x + Math.cos(a) * j * 0.13,
          1.55,
          z + Math.sin(a) * j * 0.13,
          0.055, 0.025, 0.16, M.darkGreen
        );
        l.rotation.y = a;
      }
    }
  }

  function pineapple(p, x, z) {
    for (let i = 0; i < 13; i++) {
      const a = i * Math.PI * 2 / 13;
      const l = sphere(
        p,
        x + Math.cos(a) * 0.25,
        0.26,
        z + Math.sin(a) * 0.25,
        0.075, 0.35, 0.055, M.darkGreen
      );
      l.rotation.z = Math.cos(a) * 0.55;
      l.rotation.x = Math.sin(a) * 0.55;
    }

    sphere(p, x, 0.52, z,
      0.2, 0.31, 0.2, M.orange);

    for (let i = 0; i < 6; i++) {
      const a = i * Math.PI / 3;
      const crown = sphere(
        p,
        x + Math.cos(a) * 0.07,
        0.86,
        z + Math.sin(a) * 0.07,
        0.035, 0.18, 0.03, M.green
      );
      crown.rotation.z = Math.cos(a) * 0.35;
    }
  }

  function banana(p, x, z) {
    cylinder(p, x, 1.15, z,
      2.3, 0.2, M.paleStem);

    for (let i = 0; i < 8; i++) {
      const a = i * Math.PI / 4;
      const l = sphere(
        p,
        x + Math.cos(a) * 0.8,
        2.35,
        z + Math.sin(a) * 0.8,
        0.26, 0.055, 1.1, M.bananaGreen
      );
      l.rotation.y = a;
      l.rotation.z = Math.cos(a) * 0.18;
    }

    for (let i = 0; i < 6; i++) {
      sphere(
        p,
        x + 0.37 + Math.cos(i * 1.2) * 0.09,
        1.8 - i * 0.11,
        z + 0.18,
        0.08, 0.15, 0.08, M.yellow
      );
    }
  }

  function coconut(p, x, z) {
    const trunk = cylinder(
      p, x, 2, z, 4, 0.17, M.stem
    );
    trunk.rotation.z = 0.07;

    for (let i = 0; i < 11; i++) {
      const a = i * Math.PI * 2 / 11;
      const frond = sphere(
        p,
        x + Math.cos(a) * 1.2,
        3.95,
        z + Math.sin(a) * 1.2,
        0.15, 0.065, 1.4, M.darkGreen
      );
      frond.rotation.y = a;
      frond.rotation.z = Math.cos(a) * 0.18;
    }

    for (let i = 0; i < 4; i++) {
      const a = i * Math.PI / 2;
      sphere(
        p,
        x + Math.cos(a) * 0.22,
        3.65,
        z + Math.sin(a) * 0.22,
        0.17, 0.17, 0.17, M.stem
      );
    }
  }

  function durian(p, x, z) {
    cylinder(p, x, 1.5, z,
      3, 0.24, M.stem);

    for (let i = 0; i < 7; i++) {
      const a = i * Math.PI * 2 / 7;
      sphere(
        p,
        x + Math.cos(a) * 0.75,
        3.25,
        z + Math.sin(a) * 0.75,
        0.95, 0.75, 0.9,
        i % 2 ? M.darkGreen : M.green
      );
    }

    for (let i = 0; i < 5; i++) {
      const a = i * Math.PI * 2 / 5;
      sphere(
        p,
        x + Math.cos(a) * 0.7,
        2.3,
        z + Math.sin(a) * 0.7,
        0.18, 0.22, 0.18, M.orange
      );
    }
  }

  const builders = {
    rice,
    maize,
    mung_bean: mungBean,
    groundnut,
    soybean,
    sweet_potato: sweetPotato,
    cassava,
    pineapple,
    banana,
    coconut,
    durian
  };

  // ==========================================
  // 7. FARM STATE
  // ==========================================

  const state = {
    crop: "rice",
    baseline: "rice",
    preferredCrop: "auto",
    drainage: "unknown",
    soilCover: false,
    priority: "soil",
    mode: "baseline",
    stages: [],
    stageIndex: 0,
    rainfall: null,
    temperature: null,
    climatePeriod: null
  };

  // ==========================================
  // 8. FIELD MANAGEMENT
  // ==========================================

  const hotspots = [];

  function addHotspot(x, y, z, title, explanation) {
    const object = sphere(
      hotspotGroup,
      x, y, z,
      0.22, 0.22, 0.22, M.warning
    );

    object.userData = {
      title,
      explanation
    };

    hotspots.push(object);
  }

  function addManagement(id) {
    clearGroup(managementGroup);
    clearGroup(hotspotGroup);
    hotspots.length = 0;

    const crop = CROPS[id];
    const flooded = crop.system === "paddy";
    const raised = crop.system === "raised";
    const orchard = (
      crop.system === "orchard" ||
      crop.system === "plantation"
    );

    plots.forEach(([x, z]) => {
      box(
        managementGroup,
        7.5, 0.28, 6.3,
        M.darkSoil, x, 0.18, z
      );

      if (flooded) {
        box(
          managementGroup,
          7.1, 0.06, 5.9,
          M.water, x, 0.37, z
        );

        // Paddy bunds
        for (const dz of [-3, 3]) {
          box(
            managementGroup,
            7.5, 0.22, 0.25,
            M.raisedSoil, x, 0.48, z + dz
          );
        }

      } else if (raised) {
        for (let row = -2; row <= 2; row++) {
          box(
            managementGroup,
            6.7, 0.23, 0.65,
            M.raisedSoil,
            x, 0.45, z + row * 1.05
          );
        }

      } else {
        box(
          managementGroup,
          7.1, 0.08, 5.9,
          M.soil, x, 0.36, z
        );
      }

      if (state.soilCover && !flooded) {
        for (let i = 0; i < 6; i++) {
          box(
            managementGroup,
            0.75, 0.025, 0.24,
            M.mulch,
            x - 2.5 + i,
            raised ? 0.59 : 0.42,
            z + 2.3
          );
        }
      }
    });

    if (flooded) {
      addHotspot(
        -8, 0.7, -6,
        "Paddy water management",
        "Illustrative standing water and bunds. Water depth and irrigation needs are not calculated."
      );
    }

    if (raised) {
      addHotspot(
        -5, 0.9, -4,
        "Raised planting beds",
        "Raised beds may support drainage and crop establishment. Their suitability depends on actual soil and field conditions."
      );
    }

    if (orchard) {
      addHotspot(
        5, 1.1, 4,
        "Long-term planting arrangement",
        "This crop requires longer-term field planning. Illustrated tree spacing is not a planting-density prescription."
      );
    }

    addHotspot(
      -10.1, 0.65, 0,
      "Drainage and irrigation channel",
      state.drainage === "poor"
        ? "You reported poor drainage. Inspect waterlogging and assess drainage feasibility before switching to sensitive crops."
        : state.drainage === "unknown"
          ? "Field drainage has not been verified. Observe how long water remains after heavy rain."
          : "This is an illustrative water-management channel. Actual design requires local assessment."
    );

    if (state.soilCover && !flooded) {
      addHotspot(
        4, 0.8, -4,
        "Soil-cover management",
        "Mulch and crop residues may help reduce exposed soil. Soil-health improvements are not measured by this viewer."
      );
    }
  }

  // ==========================================
  // 9. RENDER SELECTED CROP
  // ==========================================

  function showCrop(id) {
    if (!builders[id]) id = "rice";

    state.crop = id;
    clearGroup(cropGroup);
    addManagement(id);

    const crop = CROPS[id];
    const spacing = crop.spacing;

    plots.forEach(([px, pz]) => {
      const group = new THREE.Group();
      group.position.set(px, 0.49, pz);
      cropGroup.add(group);

      for (
        let x = -2.7;
        x <= 2.7;
        x += spacing
      ) {
        for (
          let z = -2.1;
          z <= 2.1;
          z += spacing
        ) {
          builders[id](group, x, z);
        }
      }
    });

    updateInformation();
    resize();
  }

  // ==========================================
  // 10. INFORMATION PANEL
  // ==========================================

  const information = document.createElement("div");
  information.id = "farm3dInformation";

  information.style.cssText = `
    position:absolute;
    bottom:12px;
    left:12px;
    right:12px;
    z-index:5;
    padding:13px 16px;
    border-radius:13px;
    background:#ffffffed;
    color:#10294d;
    font:13px/1.5 "Segoe UI",Arial,sans-serif;
    box-shadow:0 5px 18px #10294d20;
    pointer-events:none;
  `;

  host.appendChild(information);

  function updateInformation() {
    const crop = CROPS[state.crop];

    information.replaceChildren();

    const title = document.createElement("strong");
    title.style.fontSize = "15px";
    title.textContent = crop.name;

    const description = document.createElement("div");
    description.textContent = crop.explanation;

    information.append(title, description);

    if (Number.isFinite(state.rainfall)) {
      const evidence = document.createElement("div");
      evidence.style.marginTop = "5px";
      evidence.style.color = "#216ad6";
      evidence.textContent =
        `NASA historical annual rainfall: ` +
        `${state.rainfall.toFixed(1)} mm` +
        (state.climatePeriod
          ? ` · ${state.climatePeriod}`
          : "");
      information.append(evidence);
    }
  }

  // ==========================================
  // 11. CLICKABLE FIELD FEATURES
  // ==========================================

  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();

  const popup = document.createElement("div");

  popup.style.cssText = `
    position:absolute;
    top:12px;
    right:12px;
    z-index:10;
    width:min(270px,70%);
    background:#10294df2;
    color:white;
    padding:15px;
    border-radius:13px;
    font:13px/1.55 "Segoe UI",Arial,sans-serif;
    display:none;
    box-shadow:0 8px 25px #10294d35;
  `;

  const popupTitle = document.createElement("strong");
  const popupText = document.createElement("p");
  const popupClose = document.createElement("button");

  popupClose.textContent = "Close";
  popupClose.style.cssText = `
    margin-top:10px;
    background:#ffffff25;
    color:white;
    border:1px solid #ffffff50;
    padding:6px 12px;
    border-radius:8px;
    cursor:pointer;
  `;

  popupClose.onclick = () => {
    popup.style.display = "none";
  };

  popup.append(popupTitle, popupText, popupClose);
  host.appendChild(popup);

  let pointerDown = null;

  renderer.domElement.addEventListener(
    "pointerdown",
    event => {
      pointerDown = {
        x: event.clientX,
        y: event.clientY
      };
    }
  );

  renderer.domElement.addEventListener(
    "pointerup",
    event => {
      if (!pointerDown) return;

      const distance = Math.hypot(
        event.clientX - pointerDown.x,
        event.clientY - pointerDown.y
      );

      pointerDown = null;

      // Do not treat camera dragging as clicking.
      if (distance > 6) return;

      const rect =
        renderer.domElement.getBoundingClientRect();

      pointer.x =
        ((event.clientX - rect.left) / rect.width) * 2 - 1;

      pointer.y =
        -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(pointer, camera);

      const intersections = raycaster.intersectObjects(
        hotspots,
        false
      );

      if (!intersections.length) return;

      const selected = intersections[0].object;

      popupTitle.textContent =
        selected.userData.title;

      popupText.textContent =
        selected.userData.explanation;

      popup.style.display = "block";
    }
  );

  // ==========================================
  // 12. PERSONALIZED FARM SETTINGS
  // ==========================================

  function setScenario(settings = {}) {
    if (
      settings.baseline &&
      CROPS[settings.baseline]
    ) {
      state.baseline = settings.baseline;
    }

    if (
      settings.preferred_crop &&
      (CROPS[settings.preferred_crop] ||
       settings.preferred_crop === "auto")
    ) {
      state.preferredCrop = settings.preferred_crop;
    }

    if (
      ["unknown", "poor", "moderate", "good"]
        .includes(settings.drainage)
    ) {
      state.drainage = settings.drainage;
    }

    if (
      ["soil", "water", "resilience", "income"]
        .includes(settings.priority)
    ) {
      state.priority = settings.priority;
    }

    if (typeof settings.soilCover === "boolean") {
      state.soilCover = settings.soilCover;
    }

    if (Array.isArray(settings.stages)) {
      state.stages = settings.stages.filter(
        stage => CROPS[stage.crop_id]
      );
    }

    if (settings.mode === "baseline" ||
        settings.mode === "proposed") {
      state.mode = settings.mode;
    }

    const nextCrop =
      settings.crop_id && CROPS[settings.crop_id]
        ? settings.crop_id
        : state.mode === "baseline"
          ? state.baseline
          : state.stages[0]?.crop_id ||
            (CROPS[state.preferredCrop]
              ? state.preferredCrop
              : state.baseline);

    showCrop(nextCrop);
  }

  function setMode(mode) {
    if (!["baseline", "proposed"].includes(mode)) {
      return;
    }

    state.mode = mode;

    if (mode === "baseline") {
      showCrop(state.baseline);
    } else {
      const crop =
        state.stages[state.stageIndex]?.crop_id ||
        (CROPS[state.preferredCrop]
          ? state.preferredCrop
          : state.baseline);

      showCrop(crop);
    }
  }

  function showStage(index) {
    if (
      !Number.isInteger(index) ||
      index < 0 ||
      index >= state.stages.length
    ) {
      return;
    }

    state.stageIndex = index;
    state.mode = "proposed";
    showCrop(state.stages[index].crop_id);
  }

  function setSoilCover(enabled) {
    state.soilCover = Boolean(enabled);
    showCrop(state.crop);
  }

  function setDrainage(drainage) {
    if (
      !["unknown", "poor", "moderate", "good"]
        .includes(drainage)
    ) {
      return;
    }

    state.drainage = drainage;
    showCrop(state.crop);
  }

  function setEvidence(evidence = {}) {
    state.rainfall =
      typeof evidence.mean_annual_rainfall_mm === "number"
        ? evidence.mean_annual_rainfall_mm
        : null;

    state.temperature =
      typeof evidence.mean_temperature_c === "number"
        ? evidence.mean_temperature_c
        : null;

    state.climatePeriod =
      evidence.climate_period || null;

    updateInformation();
  }

  // ==========================================
  // 13. RESIZE AND CAMERA
  // ==========================================

  function resize() {
    const width = host.clientWidth;
    const height = host.clientHeight;

    if (width < 2 || height < 2) return;

    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height, false);
  }

  function resetCamera() {
    camera.position.set(17, 17, 21);
    controls.target.set(0, 0.5, 0);
    controls.update();
    resize();
  }

  // ==========================================
  // 14. PUBLIC API
  // ==========================================

  window.BUMIFarm3D = {
    showCrop,
    showStage,
    setScenario,
    setMode,
    setSoilCover,
    setDrainage,
    setEvidence,
    resize,
    resetCamera,

    getCurrentCrop() {
      return state.crop;
    },

    getState() {
      return {
        ...state,
        stages: [...state.stages]
      };
    },

    getSupportedCrops() {
      return Object.keys(CROPS);
    }
  };

  // ==========================================
  // 15. INITIALIZATION
  // ==========================================

  showCrop("rice");

  const observer = new ResizeObserver(resize);
  observer.observe(host);

  window.addEventListener("resize", resize);

  function animate() {
    requestAnimationFrame(animate);
    controls.update();

    if (
      host.clientWidth > 1 &&
      host.clientHeight > 1 &&
      !host.classList.contains("hidden")
    ) {
      renderer.render(scene, camera);
    }
  }

  animate();
}
