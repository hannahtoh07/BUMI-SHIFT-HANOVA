
/*
 BUMI SHIFT 6.6
 Interactive 3D Farming SHIFT Viewer

 Compatible with existing static/index.html.

 Features:
 - Eleven distinguishable crop models
 - Crop-specific planting arrangements
 - Rice paddy versus dryland visualization
 - Soil cover and water-management context
 - Interactive rotation-stage switching
 - Orbit, zoom and camera reset

 This is a visual management scenario,
 not a measured farm reconstruction.
*/

import * as THREE from "three";
import { OrbitControls } from
  "three/addons/controls/OrbitControls.js";

const host = document.getElementById("farm3d");

if (!host) {
  console.error("BUMI SHIFT: #farm3d not found");
} else {
  initializeFarm(host);
}

function initializeFarm(host) {

  // ==========================================
  // 1. SCENE AND CAMERA
  // ==========================================

  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#b9dfec");
  scene.fog = new THREE.Fog("#b9dfec", 35, 85);

  const camera = new THREE.PerspectiveCamera(
    45, 1, 0.1, 120
  );

  camera.position.set(17, 15, 20);

  let renderer;

  try {
    renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false
    });
  } catch (error) {
    console.error("3D renderer initialization:", error);
    host.textContent =
      "The interactive farm needs a browser with WebGL support.";
    return;
  }

  renderer.setPixelRatio(
    Math.min(window.devicePixelRatio || 1, 2)
  );

  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type =
    THREE.PCFSoftShadowMap;

  renderer.outputColorSpace =
    THREE.SRGBColorSpace;

  renderer.toneMapping =
    THREE.ACESFilmicToneMapping;

  renderer.toneMappingExposure = 1.3;

  renderer.domElement.style.display = "block";
  renderer.domElement.style.width = "100%";
  renderer.domElement.style.height = "100%";

  host.prepend(renderer.domElement);

  const controls = new OrbitControls(
    camera,
    renderer.domElement
  );

  controls.enableDamping = true;
  controls.dampingFactor = 0.07;
  controls.target.set(0, 0, 0);
  controls.minDistance = 6;
  controls.maxDistance = 48;
  controls.maxPolarAngle = Math.PI * 0.48;

  // ==========================================
  // 2. LIGHTING
  // ==========================================

  scene.add(
    new THREE.HemisphereLight(
      0xffffff,
      0x607b58,
      2.4
    )
  );

  const sunlight = new THREE.DirectionalLight(
    0xfff1d9,
    3.0
  );

  sunlight.position.set(-10, 20, 12);
  sunlight.castShadow = true;
  sunlight.shadow.mapSize.set(1024, 1024);

  sunlight.shadow.camera.left = -20;
  sunlight.shadow.camera.right = 20;
  sunlight.shadow.camera.top = 20;
  sunlight.shadow.camera.bottom = -20;

  scene.add(sunlight);

  // ==========================================
  // 3. MATERIALS AND HELPERS
  // ==========================================

  function mat(color, extra = {}) {
    return new THREE.MeshStandardMaterial({
      color,
      roughness: 0.82,
      ...extra
    });
  }

  const M = {
    grass: mat("#6eaa62"),
    soil: mat("#926443"),
    darkSoil: mat("#62452f"),
    drySoil: mat("#a9794c"),
    path: mat("#d7bc91"),
    rice: mat("#40964d"),
    riceLight: mat("#89ca61"),
    leaf: mat("#55a958"),
    darkLeaf: mat("#287746"),
    bananaLeaf: mat("#4eac5b"),
    trunk: mat("#78543c"),
    bananaStem: mat("#81ae65"),
    grain: mat("#e9cb65"),
    yellow: mat("#edc34f"),
    orange: mat("#d9a04b"),
    purple: mat("#82539a"),
    cassavaStem: mat("#927258"),
    wall: mat("#e9d5b5"),
    roof: mat("#ac6c48"),
    white: mat("#ffffff"),
    water: mat("#49b8db", {
      roughness: 0.22,
      transparent: true,
      opacity: 0.78
    })
  };

  const cropGroup = new THREE.Group();
  scene.add(cropGroup);

  const managementGroup = new THREE.Group();
  scene.add(managementGroup);

  function mesh(geometry, material, parent) {
    const object = new THREE.Mesh(
      geometry,
      material
    );

    object.castShadow = true;
    object.receiveShadow = true;
    parent.add(object);

    return object;
  }

  function box(
    parent, w, h, d, material,
    x = 0, y = 0, z = 0
  ) {
    const object = mesh(
      new THREE.BoxGeometry(w, h, d),
      material,
      parent
    );

    object.position.set(x, y, z);
    return object;
  }

  function cylinder(
    parent, x, y, z,
    height, radius, material
  ) {
    const object = mesh(
      new THREE.CylinderGeometry(
        radius * 0.8,
        radius,
        height,
        8
      ),
      material,
      parent
    );

    object.position.set(x, y, z);
    return object;
  }

  function sphere(
    parent, x, y, z,
    sx, sy, sz, material
  ) {
    const object = mesh(
      new THREE.SphereGeometry(
        1, 10, 8
      ),
      material,
      parent
    );

    object.position.set(x, y, z);
    object.scale.set(sx, sy, sz);

    return object;
  }

  function leaf(
    parent, x, y, z,
    length, width, angle,
    material
  ) {
    const object = sphere(
      parent, x, y, z,
      width, 0.055, length,
      material
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
  // 4. PERMANENT FARM LANDSCAPE
  // ==========================================

  box(
    scene, 30, 0.65, 25,
    M.grass, 0, -0.65, 0
  );

  box(
    scene, 22, 0.3, 18,
    M.soil, 0, -0.16, 0
  );

  // Walking paths
  box(
    scene, 1.1, 0.1, 18,
    M.path, 0, 0.08, 0
  );

  box(
    scene, 22, 0.1, 1.0,
    M.path, 0, 0.08, 0
  );

  // Permanent perimeter channels
  box(
    scene, 0.8, 0.08, 18,
    M.water, -10.1, 0.1, 0
  );

  box(
    scene, 0.8, 0.08, 18,
    M.water, 10.1, 0.1, 0
  );

  // Farmhouse
  box(
    scene, 2.5, 1.5, 2.2,
    M.wall, -12.3, 0.65, -9.5
  );

  const roof = box(
    scene, 3.0, 0.3, 2.8,
    M.roof, -12.3, 1.55, -9.5
  );

  roof.rotation.z = -0.12;

  // Background trees
  function backgroundTree(x, z) {
    cylinder(
      scene, x, 0.8, z,
      1.7, 0.16, M.trunk
    );

    sphere(
      scene, x, 1.95, z,
      0.85, 0.8, 0.8, M.darkLeaf
    );

    sphere(
      scene, x - 0.4, 1.75, z,
      0.6, 0.55, 0.6, M.leaf
    );
  }

  for (let i = 0; i < 5; i++) {
    backgroundTree(-12, -6 + i * 3);
    backgroundTree(12, -6 + i * 3);
  }

  const plots = [
    [-5.0, -4.3],
    [5.0, -4.3],
    [-5.0, 4.3],
    [5.0, 4.3]
  ];

  // ==========================================
  // 5. DISTINCT CROP MODELS
  // ==========================================

  function rice(p, x, z) {
    for (let i = 0; i < 5; i++) {
      const a = i * Math.PI * 2 / 5;

      const stem = cylinder(
        p,
        x + Math.cos(a) * 0.07,
        0.35,
        z + Math.sin(a) * 0.07,
        0.7,
        0.018,
        M.rice
      );

      stem.rotation.z = Math.cos(a) * 0.18;

      const blade = sphere(
        p,
        x + Math.cos(a) * 0.16,
        0.48,
        z + Math.sin(a) * 0.16,
        0.045, 0.29, 0.04,
        M.riceLight
      );

      blade.rotation.z = Math.cos(a) * 0.4;
    }

    for (let i = 0; i < 4; i++) {
      sphere(
        p, x + i * 0.035 - 0.05,
        0.75, z,
        0.035, 0.07, 0.035,
        M.grain
      );
    }
  }

  function maize(p, x, z) {
    cylinder(
      p, x, 0.85, z,
      1.7, 0.07, M.rice
    );

    for (let i = 0; i < 7; i++) {
      const a = i * 2.4;

      const l = leaf(
        p,
        x + Math.cos(a) * 0.38,
        0.55 + i * 0.14,
        z + Math.sin(a) * 0.38,
        0.6, 0.11, a,
        M.darkLeaf
      );

      l.rotation.z = Math.cos(a) * 0.24;
    }

    sphere(
      p, x + 0.16, 1.1, z,
      0.14, 0.3, 0.13,
      M.yellow
    );
  }

  function mungBean(p, x, z) {
    cylinder(
      p, x, 0.32, z,
      0.65, 0.035, M.rice
    );

    for (let i = 0; i < 3; i++) {
      const a = i * Math.PI * 2 / 3;

      for (let j = 0; j < 3; j++) {
        sphere(
          p,
          x + Math.cos(a) * (0.16 + j * 0.08),
          0.36 + j * 0.055,
          z + Math.sin(a) * (0.16 + j * 0.08),
          0.13, 0.045, 0.11,
          M.leaf
        );
      }
    }

    sphere(
      p, x + 0.18, 0.28, z,
      0.04, 0.17, 0.045,
      M.darkLeaf
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
        0.32, 0.025, M.rice
      );

      for (let j = 0; j < 3; j++) {
        sphere(
          p,
          x + Math.cos(a) * (0.18 + j * 0.08),
          0.27,
          z + Math.sin(a) * (0.18 + j * 0.08),
          0.1, 0.035, 0.08,
          M.leaf
        );
      }
    }

    for (let i = 0; i < 3; i++) {
      sphere(
        p, x + i * 0.12 - 0.12,
        0.06, z,
        0.08, 0.055, 0.06,
        M.orange
      );
    }
  }

  function soybean(p, x, z) {
    cylinder(
      p, x, 0.53, z,
      1.05, 0.045, M.rice
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
          M.darkLeaf
        );
      }
    }

    for (let i = 0; i < 3; i++) {
      sphere(
        p, x + 0.11, 0.3 + i * 0.2, z,
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
          M.leaf
        );
      }
    }

    // Purple vine flowers
    sphere(
      p, x + 0.15, 0.18, z,
      0.07, 0.04, 0.07,
      M.purple
    );
  }

  function cassava(p, x, z) {
    cylinder(
      p, x, 0.8, z,
      1.6, 0.065, M.cassavaStem
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
          M.darkLeaf
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
        M.darkLeaf
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
        M.rice
      );

      crown.rotation.z = Math.cos(a) * 0.35;
    }
  }

  function banana(p, x, z) {
    // Short, thick green pseudostem
    cylinder(
      p, x, 1.15, z,
      2.3, 0.2, M.bananaStem
    );

    // Broad banana leaves
    for (let i = 0; i < 8; i++) {
      const a = i * Math.PI / 4;

      const l = sphere(
        p,
        x + Math.cos(a) * 0.8,
        2.35,
        z + Math.sin(a) * 0.8,
        0.26, 0.055, 1.1,
        M.bananaLeaf
      );

      l.rotation.y = a;
      l.rotation.z = Math.cos(a) * 0.18;
    }

    // Hanging banana bunch
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
    // Tall brown palm trunk
    const trunk = cylinder(
      p, x, 2.0, z,
      4.0, 0.17, M.trunk
    );

    trunk.rotation.z = 0.07;

    // Radial coconut palm fronds
    for (let i = 0; i < 11; i++) {
      const a = i * Math.PI * 2 / 11;

      const frond = sphere(
        p,
        x + Math.cos(a) * 1.2,
        3.95,
        z + Math.sin(a) * 1.2,
        0.15, 0.065, 1.4,
        M.darkLeaf
      );

      frond.rotation.y = a;
      frond.rotation.z = Math.cos(a) * 0.18;
    }

    // Coconuts
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
    // Woody trunk
    cylinder(
      p, x, 1.5, z,
      3.0, 0.24, M.trunk
    );

    // Dense, rounded tree canopy
    for (let i = 0; i < 7; i++) {
      const a = i * Math.PI * 2 / 7;

      sphere(
        p,
        x + Math.cos(a) * 0.75,
        3.25,
        z + Math.sin(a) * 0.75,
        0.95, 0.75, 0.9,
        i % 2 ? M.darkLeaf : M.leaf
      );
    }

    // Hanging durian fruits
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

  const cropBuilders = {
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
  // 6. FIELD MANAGEMENT VISUALIZATION
  // ==========================================

  function addManagement(id) {
    clearGroup(managementGroup);

    const flooded = id === "rice";

    const raisedBeds = [
      "sweet_potato",
      "cassava",
      "groundnut",
      "pineapple"
    ].includes(id);

    plots.forEach(([x, z]) => {

      // Plot boundary
      box(
        managementGroup,
        7.5, 0.28, 6.3,
        M.darkSoil,
        x, 0.18, z
      );

      if (flooded) {
        // Shallow illustrative paddy water
        box(
          managementGroup,
          7.1, 0.06, 5.9,
          M.water,
          x, 0.37, z
        );

      } else if (raisedBeds) {
        // Raised planting rows
        for (let row = -2; row <= 2; row++) {
          box(
            managementGroup,
            6.7, 0.22, 0.62,
            M.drySoil,
            x, 0.43,
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
    });

    return {
      flooded,
      raisedBeds
    };
  }

  // ==========================================
  // 7. RENDER CROPS
  // ==========================================

  let currentCrop = "rice";

  function showCrop(id) {
    if (!cropBuilders[id]) id = "rice";

    currentCrop = id;

    clearGroup(cropGroup);

    const management = addManagement(id);
    const builder = cropBuilders[id];

    let spacing = 0.8;

    if (id === "maize") spacing = 1.3;
    if (id === "cassava") spacing = 1.45;
    if (id === "banana") spacing = 2.7;
    if (id === "coconut") spacing = 3.5;
    if (id === "durian") spacing = 3.2;
    if (id === "pineapple") spacing = 1.15;

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
          builder(group, x, z);
        }
      }
    });

    const name = id
      .replaceAll("_", " ")
      .replace(/\b\w/g, c => c.toUpperCase());

    if (management.flooded) {
      statusLabel.textContent =
        name + " · Paddy water-management scenario";

    } else if (management.raisedBeds) {
      statusLabel.textContent =
        name + " · Raised-bed planting scenario";

    } else {
      statusLabel.textContent =
        name + " · Field planting scenario";
    }

    resize();
  }

  // ==========================================
  // 8. STATUS LABEL
  // ==========================================

  const statusLabel = document.createElement("div");

  statusLabel.style.cssText = `
    position:absolute;
    left:12px;
    bottom:12px;
    z-index:5;
    background:#10294de8;
    color:white;
    padding:10px 14px;
    border-radius:11px;
    font:600 12px "Segoe UI",Arial,sans-serif;
    pointer-events:none;
    max-width:75%;
  `;

  host.appendChild(statusLabel);

  // ==========================================
  // 9. RESIZE AND CAMERA
  // ==========================================

  function resize() {
    const width = host.clientWidth;
    const height = host.clientHeight;

    if (width < 2 || height < 2) return;

    camera.aspect = width / height;
    camera.updateProjectionMatrix();

    renderer.setSize(
      width,
      height,
      false
    );
  }

  function resetCamera() {
    camera.position.set(17, 15, 20);
    controls.target.set(0, 0, 0);
    controls.update();
    resize();
  }

  // ==========================================
  // 10. PUBLIC DASHBOARD API
  // ==========================================

  window.BUMIFarm3D = {
    showCrop,
    resize,
    resetCamera,
    getCurrentCrop() {
      return currentCrop;
    }
  };

  // Initialize farm
  showCrop("rice");

  const observer = new ResizeObserver(resize);
  observer.observe(host);

  window.addEventListener("resize", resize);

  function animate() {
    requestAnimationFrame(animate);
    controls.update();

    // Avoid unnecessary rendering while hidden.
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
