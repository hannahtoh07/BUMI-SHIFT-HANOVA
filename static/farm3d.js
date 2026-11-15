
/*
 BUMI SHIFT 7.1
 Interactive 3D Farming SHIFT Planner
 HANOVA | Sarawak, Malaysia

 Compatible with BUMI SHIFT 7.1 index.html.

 Features:
 - 11 distinct crop models
 - Current farm vs proposed SHIFT
 - Crop rotation stage switching
 - Visible crop development timeline
 - Raised beds, paddy water, orchard spacing
 - Visible soil-cover management
 - Farmer-reported drainage interpretation
 - Clickable field-management hotspots
 - NASA historical climate context
 - Camera orbit, zoom and reset

 SCIENTIFIC DISCLOSURE:
 This is an illustrative 3D planning tool.
 It is not a digital twin, growth simulation,
 measured farm reconstruction, or prediction.
*/

import * as THREE from "three";
import { OrbitControls } from
  "three/addons/controls/OrbitControls.js";

const host = document.getElementById("farm3d");

if (host) initializeFarm(host);

function initializeFarm(host) {

  // ==========================================
  // 1. CROP LIBRARY
  // ==========================================

  const CROPS = {
    rice: {
      name: "Rice",
      system: "paddy",
      duration: 4,
      spacing: 0.65,
      matureHeight: 0.75,
      info: "Managed paddy water and bunds may be used."
    },
    maize: {
      name: "Maize",
      system: "rows",
      duration: 4,
      spacing: 1.25,
      matureHeight: 1.8,
      info: "Rows, drainage and moisture during flowering matter."
    },
    mung_bean: {
      name: "Mung Bean",
      system: "rows",
      duration: 3,
      spacing: 0.9,
      matureHeight: 0.7,
      info: "Legume establishment and nodulation require review."
    },
    groundnut: {
      name: "Groundnut",
      system: "raised",
      duration: 4,
      spacing: 0.95,
      matureHeight: 0.45,
      info: "Suitable soil structure supports pegging and pods."
    },
    soybean: {
      name: "Soybean",
      system: "rows",
      duration: 4,
      spacing: 1.0,
      matureHeight: 1.1,
      info: "Crop-family diversification and nodulation matter."
    },
    sweet_potato: {
      name: "Sweet Potato",
      system: "raised",
      duration: 4,
      spacing: 1.0,
      matureHeight: 0.3,
      info: "Raised beds may improve field drainage."
    },
    cassava: {
      name: "Cassava",
      system: "raised",
      duration: 10,
      spacing: 1.6,
      matureHeight: 1.7,
      info: "Longer field occupation and erosion control matter."
    },
    pineapple: {
      name: "Pineapple",
      system: "raised",
      duration: 16,
      spacing: 1.25,
      matureHeight: 0.95,
      info: "Long-duration field planning and drainage matter."
    },
    banana: {
      name: "Banana",
      system: "plantation",
      duration: 12,
      spacing: 3.0,
      matureHeight: 2.8,
      info: "Wind exposure, drainage and disease management matter."
    },
    coconut: {
      name: "Coconut",
      system: "orchard",
      duration: 36,
      spacing: 4.0,
      matureHeight: 4.3,
      info: "This is a long-term plantation establishment scenario."
    },
    durian: {
      name: "Durian",
      system: "orchard",
      duration: 60,
      spacing: 3.8,
      matureHeight: 4.0,
      info: "This is a long-term orchard establishment scenario."
    }
  };

  // ==========================================
  // 2. SCENE, CAMERA AND RENDERER
  // ==========================================

  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#b9dfef");
  scene.fog = new THREE.Fog("#b9dfef", 35, 85);

  const camera = new THREE.PerspectiveCamera(
    43, 1, 0.1, 120
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
      "This visualization requires WebGL support.";
    return;
  }

  renderer.setPixelRatio(
    Math.min(window.devicePixelRatio || 1, 2)
  );

  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.25;

  renderer.domElement.style.width = "100%";
  renderer.domElement.style.height = "100%";
  renderer.domElement.style.display = "block";

  host.prepend(renderer.domElement);

  const controls = new OrbitControls(
    camera,
    renderer.domElement
  );

  controls.enableDamping = true;
  controls.target.set(0, 0.5, 0);
  controls.minDistance = 7;
  controls.maxDistance = 48;
  controls.maxPolarAngle = Math.PI * 0.49;

  scene.add(new THREE.HemisphereLight(
    0xffffff, 0x5d805b, 2.3
  ));

  const sun = new THREE.DirectionalLight(
    0xfff1d6, 2.8
  );

  sun.position.set(-9, 20, 12);
  sun.castShadow = true;
  sun.shadow.mapSize.set(1024, 1024);
  sun.shadow.camera.left = -22;
  sun.shadow.camera.right = 22;
  sun.shadow.camera.top = 22;
  sun.shadow.camera.bottom = -22;
  scene.add(sun);

  // ==========================================
  // 3. MATERIALS
  // ==========================================

  function mat(color, extra = {}) {
    return new THREE.MeshStandardMaterial({
      color,
      roughness: 0.82,
      ...extra
    });
  }

  const M = {
    grass: mat("#72ad65"),
    soil: mat("#936644"),
    darkSoil: mat("#60412d"),
    raised: mat("#ad7850"),
    path: mat("#dec69a"),
    green: mat("#459a4c"),
    lightGreen: mat("#8bce66"),
    darkGreen: mat("#287746"),
    bananaGreen: mat("#53b263"),
    paleStem: mat("#89ae6d"),
    trunk: mat("#7b573e"),
    grain: mat("#e8ca62"),
    yellow: mat("#edc955"),
    orange: mat("#dba04b"),
    purple: mat("#8553a0"),
    wall: mat("#e9d6b8"),
    roof: mat("#b16f4d"),
    mulch: mat("#edca76"),
    residue: mat("#d7ae60"),
    warning: mat("#f4a937", {
      emissive: "#b15c00",
      emissiveIntensity: 0.3
    }),
    water: mat("#4abce2", {
      roughness: 0.2,
      transparent: true,
      opacity: 0.72
    })
  };

  // ==========================================
  // 4. GEOMETRY HELPERS
  // ==========================================

  function mesh(parent, geometry, material) {
    const obj = new THREE.Mesh(
      geometry,
      material
    );

    obj.castShadow = true;
    obj.receiveShadow = true;
    parent.add(obj);

    return obj;
  }

  function box(
    parent, w, h, d, material,
    x = 0, y = 0, z = 0
  ) {
    const obj = mesh(
      parent,
      new THREE.BoxGeometry(w, h, d),
      material
    );
    obj.position.set(x, y, z);
    return obj;
  }

  function cylinder(
    parent, x, y, z,
    height, radius, material
  ) {
    const obj = mesh(
      parent,
      new THREE.CylinderGeometry(
        radius * 0.8,
        radius,
        height,
        7
      ),
      material
    );
    obj.position.set(x, y, z);
    return obj;
  }

  function sphere(
    parent, x, y, z,
    sx, sy, sz, material
  ) {
    const obj = mesh(
      parent,
      new THREE.SphereGeometry(1, 9, 7),
      material
    );

    obj.position.set(x, y, z);
    obj.scale.set(sx, sy, sz);
    return obj;
  }

  function leaf(
    parent, x, y, z,
    length, width, angle, material
  ) {
    const obj = sphere(
      parent, x, y, z,
      width, 0.045, length,
      material
    );
    obj.rotation.y = angle;
    return obj;
  }

  function clearGroup(group) {
    group.traverse(obj => {
      if (obj.isMesh) {
        obj.geometry.dispose();
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

  box(scene, 1.1, 0.12, 18, M.path, 0, 0.08, 0);
  box(scene, 22, 0.12, 1.0, M.path, 0, 0.08, 0);

  // Perimeter water-management channels
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
    cylinder(
      scene, x, 0.85, z,
      1.7, 0.15, M.trunk
    );

    sphere(
      scene, x, 2, z,
      0.8, 0.8, 0.8, M.darkGreen
    );

    sphere(
      scene, x - 0.4, 1.8, z,
      0.55, 0.5, 0.55, M.green
    );
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
  // 6. ELEVEN CROP MODELS
  // ==========================================

  function rice(p, x, z) {
    for (let i = 0; i < 5; i++) {
      const a = i * Math.PI * 2 / 5;
      const dx = Math.cos(a);
      const dz = Math.sin(a);

      const stem = cylinder(
        p,
        x + dx * 0.08,
        0.32,
        z + dz * 0.08,
        0.64,
        0.018,
        M.green
      );

      stem.rotation.z = dx * 0.2;

      const blade = sphere(
        p,
        x + dx * 0.17,
        0.46,
        z + dz * 0.17,
        0.04, 0.27, 0.04,
        M.lightGreen
      );

      blade.rotation.z = dx * 0.45;
    }

    for (let i = 0; i < 4; i++) {
      sphere(
        p,
        x + i * 0.04 - 0.06,
        0.72,
        z,
        0.035, 0.07, 0.035,
        M.grain
      );
    }
  }

  function maize(p, x, z) {
    cylinder(
      p, x, 0.85, z,
      1.7, 0.07, M.green
    );

    for (let i = 0; i < 7; i++) {
      const a = i * 2.4;

      const l = leaf(
        p,
        x + Math.cos(a) * 0.38,
        0.55 + i * 0.14,
        z + Math.sin(a) * 0.38,
        0.6, 0.12, a,
        M.darkGreen
      );

      l.rotation.z = Math.cos(a) * 0.25;
    }

    sphere(
      p, x + 0.16, 1.12, z,
      0.14, 0.3, 0.13, M.yellow
    );
  }

  function mungBean(p, x, z) {
    cylinder(
      p, x, 0.32, z,
      0.64, 0.035, M.green
    );

    for (let i = 0; i < 3; i++) {
      const a = i * Math.PI * 2 / 3;

      for (let j = 0; j < 3; j++) {
        sphere(
          p,
          x + Math.cos(a) * (0.17 + j * 0.08),
          0.35 + j * 0.055,
          z + Math.sin(a) * (0.17 + j * 0.08),
          0.13, 0.045, 0.11,
          M.lightGreen
        );
      }
    }

    sphere(
      p, x + 0.18, 0.28, z,
      0.04, 0.17, 0.045,
      M.darkGreen
    );
  }

  function groundnut(p, x, z) {
    for (let i = 0; i < 6; i++) {
      const a = i * Math.PI / 3;

      cylinder(
        p,
        x + Math.cos(a) * 0.1,
        0.16,
        z + Math.sin(a) * 0.1,
        0.32, 0.025, M.green
      );

      for (let j = 0; j < 3; j++) {
        sphere(
          p,
          x + Math.cos(a) * (0.18 + j * 0.08),
          0.27,
          z + Math.sin(a) * (0.18 + j * 0.08),
          0.1, 0.035, 0.08,
          M.lightGreen
        );
      }
    }

    for (let i = 0; i < 3; i++) {
      sphere(
        p,
        x + i * 0.12 - 0.12,
        0.06, z,
        0.08, 0.055, 0.06,
        M.orange
      );
    }
  }

  function soybean(p, x, z) {
    cylinder(
      p, x, 0.52, z,
      1.04, 0.045, M.green
    );

    for (let i = 0; i < 5; i++) {
      const a = i * 1.25;

      for (let j = 0; j < 3; j++) {
        sphere(
          p,
          x + Math.cos(a) * (0.17 + j * 0.1),
          0.4 + j * 0.16,
          z + Math.sin(a) * (0.17 + j * 0.1),
          0.16, 0.05, 0.13,
          M.darkGreen
        );
      }
    }

    for (let i = 0; i < 3; i++) {
      sphere(
        p,
        x + 0.11,
        0.3 + i * 0.2,
        z,
        0.07, 0.13, 0.055,
        M.yellow
      );
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
          0.16, 0.035, 0.13,
          M.green
        );
      }
    }

    sphere(
      p, x + 0.15, 0.18, z,
      0.07, 0.04, 0.07,
      M.purple
    );
  }

  function cassava(p, x, z) {
    cylinder(
      p, x, 0.8, z,
      1.6, 0.065, M.trunk
    );

    for (let i = 0; i < 8; i++) {
      const a = i * Math.PI / 4;

      for (let j = 1; j <= 5; j++) {
        const l = sphere(
          p,
          x + Math.cos(a) * j * 0.13,
          1.55,
          z + Math.sin(a) * j * 0.13,
          0.055, 0.025, 0.16,
          M.darkGreen
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
        0.075, 0.35, 0.055,
        M.darkGreen
      );

      l.rotation.z = Math.cos(a) * 0.55;
      l.rotation.x = Math.sin(a) * 0.55;
    }

    sphere(
      p, x, 0.52, z,
      0.2, 0.31, 0.2,
      M.orange
    );

    for (let i = 0; i < 6; i++) {
      const a = i * Math.PI / 3;

      const crown = sphere(
        p,
        x + Math.cos(a) * 0.07,
        0.86,
        z + Math.sin(a) * 0.07,
        0.035, 0.18, 0.03,
        M.green
      );

      crown.rotation.z = Math.cos(a) * 0.35;
    }
  }

  function banana(p, x, z) {
    cylinder(
      p, x, 1.15, z,
      2.3, 0.2, M.paleStem
    );

    for (let i = 0; i < 8; i++) {
      const a = i * Math.PI / 4;

      const l = sphere(
        p,
        x + Math.cos(a) * 0.8,
        2.35,
        z + Math.sin(a) * 0.8,
        0.26, 0.055, 1.1,
        M.bananaGreen
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
        0.08, 0.15, 0.08,
        M.yellow
      );
    }
  }

  function coconut(p, x, z) {
    const trunk = cylinder(
      p, x, 2, z,
      4, 0.17, M.trunk
    );

    trunk.rotation.z = 0.07;

    for (let i = 0; i < 11; i++) {
      const a = i * Math.PI * 2 / 11;

      const frond = sphere(
        p,
        x + Math.cos(a) * 1.2,
        3.95,
        z + Math.sin(a) * 1.2,
        0.15, 0.065, 1.4,
        M.darkGreen
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
        0.17, 0.17, 0.17,
        M.trunk
      );
    }
  }

  function durian(p, x, z) {
    cylinder(
      p, x, 1.5, z,
      3, 0.24, M.trunk
    );

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
        0.18, 0.22, 0.18,
        M.orange
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
    priority: "soil",
    soilCover: false,
    mode: "baseline",
    stages: [],
    stageIndex: 0,
    growth: 1,
    rainfall: null,
    temperature: null,
    climatePeriod: null
  };

  // ==========================================
  // 8. DEVELOPMENT STAGES
  // ==========================================

  function growthPhase(progress) {
    if (progress < 0.15) return "Field preparation";
    if (progress < 0.4) return "Establishment";
    if (progress < 0.75) return "Vegetative development";
    return "Later development";
  }

  function growthScale(progress) {
    if (progress < 0.15) return 0;
    return Math.max(
      0.12,
      Math.min(1, (progress - 0.1) / 0.9)
    );
  }

  // ==========================================
  // 9. FIELD MANAGEMENT
  // ==========================================

  const hotspots = [];

  function addHotspot(
    x, y, z, title, explanation
  ) {
    const obj = sphere(
      hotspotGroup,
      x, y, z,
      0.23, 0.23, 0.23,
      M.warning
    );

    obj.userData = {
      title,
      explanation
    };

    hotspots.push(obj);
  }

  function addManagement(id) {
    clearGroup(managementGroup);
    clearGroup(hotspotGroup);
    hotspots.length = 0;

    const crop = CROPS[id];
    const paddy = crop.system === "paddy";
    const raised = crop.system === "raised";
    const orchard = (
      crop.system === "orchard" ||
      crop.system === "plantation"
    );

    plots.forEach(([x, z]) => {

      box(
        managementGroup,
        7.5, 0.28, 6.3,
        M.darkSoil,
        x, 0.18, z
      );

      if (paddy) {
        box(
          managementGroup,
          7.1, 0.06, 5.9,
          M.water,
          x, 0.37, z
        );

        for (const dz of [-3, 3]) {
          box(
            managementGroup,
            7.5, 0.23, 0.25,
            M.raised,
            x, 0.48, z + dz
          );
        }

      } else if (raised) {

        for (let row = -2; row <= 2; row++) {
          box(
            managementGroup,
            6.7, 0.23, 0.65,
            M.raised,
            x, 0.45,
            z + row * 1.05
          );
        }

      } else {

        box(
          managementGroup,
          7.1, 0.08, 5.9,
          M.soil,
          x, 0.36, z
        );
      }

      // Visually distinct soil-cover scenario.
      // For dryland crops, cover most of the
      // exposed spaces between planting rows.
      if (state.soilCover && !paddy) {

        for (let row = -2; row <= 2; row++) {

          box(
            managementGroup,
            6.5, 0.035, 0.36,
            M.mulch,
            x, raised ? 0.59 : 0.43,
            z + row * 1.05 + 0.42
          );

          for (let i = -3; i <= 3; i++) {
            box(
              managementGroup,
              0.38, 0.04, 0.09,
              M.residue,
              x + i * 0.9,
              raised ? 0.62 : 0.46,
              z + row * 1.05 + 0.42
            );
          }
        }
      }
    });

    if (paddy) {
      addHotspot(
        -8, 0.7, -6,
        "Paddy water management",
        "The standing water and bunds illustrate a managed paddy scenario. Water depth and irrigation requirements are not calculated."
      );
    }

    if (raised) {
      addHotspot(
        -5, 0.9, -4,
        "Raised planting beds",
        "Raised beds may improve field drainage and establishment for suitable crops. Actual dimensions require local assessment."
      );
    }

    if (orchard) {
      addHotspot(
        5, 1.1, 4,
        "Long-term planting arrangement",
        "This crop involves a longer-term planting decision. The displayed tree spacing is illustrative, not a planting-density recommendation."
      );
    }

    addHotspot(
      -10.1, 0.65, 0,
      "Water-management channel",
      state.drainage === "poor"
        ? "You reported poor drainage. Inspect waterlogging and assess whether drainage improvements are feasible before changing crops."
        : state.drainage === "unknown"
          ? "Field drainage is unknown. Observe how long water remains after heavy rain."
          : "This channel illustrates a possible water-management feature. Actual engineering design requires site measurements."
    );

    if (state.soilCover && !paddy) {
      addHotspot(
        4, 0.8, -4,
        "Soil-cover management",
        "The golden strips represent mulch or crop residues. They may reduce exposed soil, but the visualization does not calculate soil-health improvements."
      );
    }
  }

  // ==========================================
  // 10. RENDER CROP DEVELOPMENT
  // ==========================================

  function renderCrop() {
    clearGroup(cropGroup);

    const crop = CROPS[state.crop];
    const builder = builders[state.crop];
    const scale = growthScale(state.growth);

    if (scale <= 0) {
      updateInformation();
      return;
    }

    plots.forEach(([px, pz]) => {
      const group = new THREE.Group();
      group.position.set(px, 0.49, pz);
      cropGroup.add(group);

      const spacing = crop.spacing;

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

          const plant = new THREE.Group();
          plant.position.set(x, 0, z);
          group.add(plant);

          // Crop models are built around local
          // coordinates and then scaled to show
          // simplified development.
          builder(plant, 0, 0);

          plant.scale.set(
            Math.max(0.3, scale),
            scale,
            Math.max(0.3, scale)
          );
        }
      }
    });

    updateInformation();
  }

  function showCrop(id) {
    if (!CROPS[id]) id = "rice";

    state.crop = id;

    addManagement(id);
    renderCrop();
    resize();
  }

  function setGrowth(value) {
    if (!Number.isFinite(value)) return;

    state.growth = Math.max(
      0,
      Math.min(1, value)
    );

    renderCrop();
  }

  // ==========================================
  // 11. INFORMATION PANEL
  // ==========================================

  const information = document.createElement("div");
  information.id = "farm3dInformation";

  information.style.cssText = `
    position:absolute;
    left:12px;
    right:12px;
    bottom:12px;
    z-index:5;
    background:#fffffff0;
    color:#10294d;
    border-radius:13px;
    padding:12px 15px;
    font:13px/1.5 "Segoe UI",Arial,sans-serif;
    pointer-events:none;
    box-shadow:0 5px 18px #10294d20;
  `;

  host.appendChild(information);

  function updateInformation() {
    const crop = CROPS[state.crop];
    const phase = growthPhase(state.growth);

    information.replaceChildren();

    const title = document.createElement("strong");
    title.style.fontSize = "15px";
    title.textContent =
      `${crop.name} · ${phase}`;

    const description = document.createElement("div");

    const nominalMonth = Math.max(
      1,
      Math.ceil(
        state.growth * crop.duration
      )
    );

    description.textContent =
      `Illustrative development stage near month ` +
      `${nominalMonth} of approximately ` +
      `${crop.duration} months. ${crop.info}`;

    information.append(title, description);

    if (state.soilCover) {
      const cover = document.createElement("div");
      cover.style.color = "#087b78";
      cover.style.marginTop = "5px";

      cover.textContent =
        crop.system === "paddy"
          ? "Dryland mulch is not shown for the flooded paddy scenario."
          : "Golden strips illustrate optional soil-cover management.";

      information.append(cover);
    }

    if (Number.isFinite(state.rainfall)) {
      const evidence = document.createElement("div");
      evidence.style.color = "#216ad6";
      evidence.style.marginTop = "5px";

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
  // 12. CLICKABLE FIELD FEATURES
  // ==========================================

  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();

  const popup = document.createElement("div");

  popup.style.cssText = `
    position:absolute;
    top:12px;
    right:12px;
    z-index:12;
    width:min(275px,75%);
    background:#10294df2;
    color:white;
    padding:15px;
    border-radius:13px;
    font:13px/1.5 "Segoe UI",Arial,sans-serif;
    display:none;
    box-shadow:0 8px 25px #10294d35;
  `;

  const popupTitle = document.createElement("strong");
  const popupText = document.createElement("p");
  const popupClose = document.createElement("button");

  popupClose.textContent = "Close";
  popupClose.style.cssText = `
    margin-top:9px;
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

  popup.append(
    popupTitle,
    popupText,
    popupClose
  );

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

      if (distance > 6) return;

      const rect =
        renderer.domElement.getBoundingClientRect();

      pointer.x =
        ((event.clientX - rect.left) /
          rect.width) * 2 - 1;

      pointer.y =
        -((event.clientY - rect.top) /
          rect.height) * 2 + 1;

      raycaster.setFromCamera(
        pointer,
        camera
      );

      const intersections =
        raycaster.intersectObjects(
          hotspots,
          false
        );

      if (!intersections.length) return;

      const data =
        intersections[0].object.userData;

      popupTitle.textContent = data.title;
      popupText.textContent = data.explanation;
      popup.style.display = "block";
    }
  );

  // ==========================================
  // 13. SCENARIO MANAGEMENT
  // ==========================================

  function setScenario(settings = {}) {

    if (CROPS[settings.baseline]) {
      state.baseline = settings.baseline;
    }

    if (
      settings.preferred_crop === "auto" ||
      CROPS[settings.preferred_crop]
    ) {
      state.preferredCrop =
        settings.preferred_crop;
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

    if (Array.isArray(settings.stages)) {
      state.stages = settings.stages.filter(
        stage => CROPS[stage.crop_id]
      );
      state.stageIndex = 0;
    }

    if (
      ["baseline", "proposed"]
        .includes(settings.mode)
    ) {
      state.mode = settings.mode;
    }

    const nextCrop =
      state.mode === "baseline"
        ? state.baseline
        : state.stages[0]?.crop_id ||
          (CROPS[state.preferredCrop]
            ? state.preferredCrop
            : state.baseline);

    state.growth = 1;
    showCrop(nextCrop);
  }

  function setMode(mode) {
    if (
      !["baseline", "proposed"]
        .includes(mode)
    ) return;

    state.mode = mode;
    state.growth = 1;

    const id =
      mode === "baseline"
        ? state.baseline
        : state.stages[state.stageIndex]?.crop_id ||
          (CROPS[state.preferredCrop]
            ? state.preferredCrop
            : state.baseline);

    showCrop(id);
  }

  function showStage(index) {
    if (
      !Number.isInteger(index) ||
      index < 0 ||
      index >= state.stages.length
    ) return;

    state.stageIndex = index;
    state.mode = "proposed";
    state.growth = 1;

    showCrop(
      state.stages[index].crop_id
    );
  }

  function setSoilCover(enabled) {
    state.soilCover = Boolean(enabled);
    addManagement(state.crop);
    updateInformation();
  }

  function setDrainage(drainage) {
    if (
      !["unknown", "poor", "moderate", "good"]
        .includes(drainage)
    ) return;

    state.drainage = drainage;
    addManagement(state.crop);
    updateInformation();
  }

  function setEvidence(data = {}) {
    state.rainfall =
      Number.isFinite(
        data.mean_annual_rainfall_mm
      )
        ? data.mean_annual_rainfall_mm
        : null;

    state.temperature =
      Number.isFinite(
        data.mean_temperature_c
      )
        ? data.mean_temperature_c
        : null;

    state.climatePeriod =
      data.climate_period || null;

    updateInformation();
  }

  // ==========================================
  // 14. CAMERA AND RESPONSIVE RENDERING
  // ==========================================

  function resize() {
    const w = host.clientWidth;
    const h = host.clientHeight;

    if (w < 2 || h < 2) return;

    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
  }

  function resetCamera() {
    camera.position.set(17, 17, 21);
    controls.target.set(0, 0.5, 0);
    controls.update();
    resize();
  }

  // ==========================================
  // 15. PUBLIC API
  // ==========================================

  window.BUMIFarm3D = {
    showCrop,
    showStage,
    setScenario,
    setMode,
    setGrowth,
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
  // 16. INITIALIZE
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
