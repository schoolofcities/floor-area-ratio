<script>
    import { onMount } from "svelte";
    import maplibregl from "maplibre-gl";
    import "../assets/styles.css";
    import "maplibre-gl/dist/maplibre-gl.css";

    import * as pmtiles from "pmtiles";
    import baseMap from "../assets/basemap.json";
    import topMap from "../assets/topmap.json";

    let MASSING_URL = "MASSING_FAR.pmtiles";
    let FAR_DATA_URL = "FAR_DATA.pmtiles";
    let FAR_PROPERTY_URL = "FAR_PROPERTY.pmtiles";

    let map;
    let is3DVisible = false;

    const scale = new maplibregl.ScaleControl({
        maxWidth: 100,
        unit: "metric",
    });

    const toggle3DVisibility = () => {
        is3DVisible = !is3DVisible;

        if (map.getLayer("massing-layer")) {
            map.setLayoutProperty(
                "massing-layer",
                "visibility",
                is3DVisible ? "visible" : "none",
            );
        }

        if (is3DVisible) {
            map.setMaxPitch(60);
            map.easeTo({
                pitch: 60,
                duration: 1000,
            });
            map.dragRotate.enable();
            map.dragRotate.setPitchWithRotate(true);
            map.touchZoomRotate.enableRotation();
        } else {
            map.easeTo({
                pitch: 0,
                duration: 1000,
            });
        }
    };

    let isTextVisible;
    const toggleTextVisibility = () => {
        isTextVisible = !isTextVisible;
    };

    let currentWidth = 0;
    let previousWidth = 0;

    function updateScreenWidth() {
        previousWidth = currentWidth;
        currentWidth = window.innerWidth;

        // Update isTextVisible based on screen width
        if (previousWidth <= 750 && currentWidth > 750) {
            isTextVisible = true;
            console.log("Text is visible");
        } else if (previousWidth > 750 && currentWidth <= 750) {
            isTextVisible = false;
            console.log("Text is hidden");
        }
    }

    onMount(async () => {
        const protocol = new pmtiles.Protocol();
        maplibregl.addProtocol("pmtiles", protocol.tile);

        map = new maplibregl.Map({
            container: "map",
            style: baseMap,
            center: [-79.409168, 43.650783],
            zoom: 11.6,
            bearing: -17,
            scrollZoom: true,
            minZoom: 10.5,
            maxPitch: 0,
            maxBounds: [
                [-79.8, 43.35],
                [-79.0, 43.9],
            ],
            attributionControl: false,
        });

        map.addControl(
            new maplibregl.NavigationControl({
                showCompass: true,
                visualizePitch: true,
            }),
            "top-right",
        );

        //MAP INTERACTIONS
        map.boxZoom.disable();

        if (window.innerWidth >= 750) {
            map.addControl(scale, "bottom-right");
        }

        // ON MOUNT TEXT DISPLAY
        if (window.innerWidth >= 750) {
            isTextVisible = true;
        }
        if (window.innerWidth < 750) {
            isTextVisible = false;
        }

        updateScreenWidth();
        window.addEventListener("resize", updateScreenWidth);

        //RESIZE EVENTS
        window.addEventListener("resize", () => {
            //MOVE SCALE BAR
            if (window.innerWidth < 750 && map.hasControl(scale)) {
                map.removeControl(scale);
            } else if (window.innerWidth >= 750 && !map.hasControl(scale)) {
                map.addControl(scale, "bottom-right");
            }
        });

        map.on("load", () => {
            //CONSOLE LOG MAP POSITION
            map.on("move", () => {
                const center = map.getCenter();
                const zoom = map.getZoom();
                const bearing = map.getBearing();
                const pitch = map.getPitch();

                console.log("Map position:", {
                    center: {
                        lng: center.lng.toFixed(6),
                        lat: center.lat.toFixed(6),
                    },
                    zoom: zoom.toFixed(2),
                    bearing: bearing.toFixed(2),
                    pitch: pitch.toFixed(2),
                });
            });

            //MAP POSITION ON MOBILE LOAD
            if (window.innerWidth < 750) {
                map.jumpTo({
                    center: [-79.374384, 43.630475],
                    zoom: 11.6,
                    bearing: -17,
                });
            }

            //BASE MAP
            topMap.forEach((e) => {
                map.addLayer(e);
            });

            // FAR COLOUR LAYER
            map.addSource("far-colour", {
                type: "vector",
                url: "pmtiles://" + FAR_PROPERTY_URL,
            });
            map.addLayer({
                id: "far-colour-layer",
                type: "fill",
                source: "far-colour",
                "source-layer": "far",
                paint: {
                    "fill-color": [
                        "case",
                        ["<", ["get", "far"], 0.1],
                        "rgba(0,0,0,0)", // 0.1 <
                        ["<", ["get", "far"], 1.0],
                        "#c8d1e5", // 0.1 - 1.0
                        ["<", ["get", "far"], 2.0],
                        "#89b6d6", // 1.0 - 2.0
                        ["<", ["get", "far"], 5.0],
                        "#499fb9", // 2.0 - 5.0
                        ["<", ["get", "far"], 15.0],
                        "#17898c", // 5.0 - 15.0
                        "#015847", // > 15.0
                    ],
                    "fill-opacity": 1,
                },
            });

            // FAR DATA
            map.addSource("far-data", {
                type: "vector",
                url: "pmtiles://" + FAR_DATA_URL,
            });
            map.addLayer({
                id: "far-data-layer",
                type: "fill",
                source: "far-data",
                "source-layer": "far",
                paint: {
                    "fill-color": "#000000",
                    "fill-opacity": 0,
                },
            });
            map.addLayer({
                id: "far-data-line",
                type: "line",
                source: "far-data",
                "source-layer": "far",
                paint: {
                    "line-color": "#fff",
                    "line-width": [
                        "interpolate",
                        ["linear"],
                        ["zoom"],
                        13.5,
                        0.1, // At zoom level 13.5, line width is 0.1
                        18,
                        1, // At zoom level 18, line width is 2.0
                    ],
                    "line-opacity": 0.5,
                },
                minzoom: 13.5,
            });

            // add zoom dependent line width
            map.addLayer({
                id: "far-data-line",
                type: "line",
                source: "far-data",
                "source-layer": "far",
                paint: {
                    "line-color": "#fff",
                    "line-width": 0.1,
                    "line-opacity": 0.5,
                },
                minzoom: 13.5,
            });

                        //MOVING ROAD LABELS TO THE TOP
                        map.moveLayer("roadname_minor");
            map.moveLayer("roadname_sec");
            map.moveLayer("roadname_pri");
            map.moveLayer("roadname_major");

            // MASSING LAYER
            map.addSource("massing", {
                type: "vector",
                url: "pmtiles://" + MASSING_URL,
            });
            map.addLayer({
                id: "massing-layer",
                type: "fill-extrusion",
                source: "massing",
                "source-layer": "buildings_split",
                paint: {
                    "fill-extrusion-color": [
                        "case",
                        ["<", ["get", "far"], 0.1],
                        "#f2f2f2", // 0.1 >
                        ["<=", ["get", "far"], 1.0],
                        "#c8d1e5", // 0.1 - 1.0
                        ["<=", ["get", "far"], 2.0],
                        "#89b6d6", // 1.0 - 2.0
                        ["<=", ["get", "far"], 5.0],
                        "#499fb9", // 2.0 - 5.0
                        ["<=", ["get", "far"], 15.0],
                        "#17898c", // 5.0 - 15.0
                        "#015847", // > 15.0
                    ],
                    "fill-extrusion-height": ["get", "AVG_HEIGHT"],
                    "fill-extrusion-base": 0,
                    "fill-extrusion-opacity": 0.9,
                },
                layout: {
                    visibility: "none",
                },
            });

            //HOVER FAR LABELS
            const popup = new maplibregl.Popup({
                closeButton: false,
                closeOnClick: false,
            });

            map.on("mousemove", "far-data-layer", (e) => {
                const currentZoom = map.getZoom();
                const minZoom = 13; // Set the minimum zoom level for labels

                if (currentZoom < minZoom) {
                    popup.remove(); // Ensure the popup is removed if zoom is less than 14
                    return; // Skip hover logic if zoom is less than 14
                }

                // Check if features exist under the cursor
                const features = e.features;
                if (features && features.length > 0) {
                    const farValue = features[0].properties.far; // Adjust property name if different
                    popup
                        .setLngLat(e.lngLat) // Set popup location
                        .setHTML(`<strong>FAR:</strong> ${farValue}`) // Set popup content
                        .addTo(map); // Add popup to the map
                }
            });

            map.on("mouseleave", "far-data-layer", () => {
                popup.remove();
            });
        });
    });
</script>

<svelte:head>
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1, minimum-scale=1"
    />
    <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
</svelte:head>

<div
    id="box"
    style="height: {isTextVisible ? 'calc(100vh - 30px)' : '240px'}; "
>
    <div class="title">
        <h3>Toronto FAR Map</h3>
    </div>

    <div class="text" style="display: {isTextVisible ? 'block' : 'none'};">
        <h4>What is Floor Area Ratio (FAR)?</h4>
        <p>
            <a href="https://jamaps.github.io/" target="_blank">Jeff Allen</a>,
            <a
                href="https://www.linkedin.com/in/scott-christian-mccallum/"
                target="_blank">Scott McCallum</a
            > | April 2025
        </p>
        <p>
            FAR is a measure of a building's total floor area relative to the
            size of its lot. It is calculated as:
        </p>
        <p class="equation">
            <math xmlns="http://www.w3.org/1998/Math/MathML">
                <mrow>
                    <mi>FAR</mi>
                    <mo>=</mo>
                    <mfrac>
                        <mrow>
                            <mi>Total Building Floor Area</mi>
                        </mrow>
                        <mrow>
                            <mi>Lot Area</mi>
                        </mrow>
                    </mfrac>
                </mrow>
            </math>
        </p>
        <p>
            Higher FAR values indicate denser development, while lower values
            suggest less intensive land use.
        </p>
        <p>
            A tall, narrow tower and a low, sprawling building can have the same
            FAR if their total floor areas are equal. Design choices like
            setbacks, height limits, and lot coverage can influence massing
            while maintaining the same FAR:
        </p>

        <p
            style="display: flex; flex-direction: column; justify-content: center; align-items: center;"
        >
            <img
                class="far-diagram"
                src="/src/assets/far-a.svg"
                alt="FAR Diagram"
            /> <small>FAR: 1.0</small>
            <img
                class="far-diagram"
                src="/src/assets/far-b.svg"
                alt="FAR Diagram"
            /> <small>FAR: 1.0</small>
            <img
                class="far-diagram"
                src="/src/assets/far-c.svg"
                alt="FAR Diagram"
            /> <small>FAR: 1.0</small>
        </p>
        <p></p>
        <h4>Methodology</h4>
        <p>
            This visualization was created using 3D massing and property
            boundary data from
            <a href="https://open.toronto.ca/" target="_blank"
                >the City of Toronto’s Open Data Portal</a
            >.
        </p>

        <p>
            For the FAR calculations, we assumed an average building floor
            height of 3 meters.
        </p>

        <h4>Data</h4>
        <ul>
            <li>
                <a
                    href="https://open.toronto.ca/dataset/3d-massing/"
                    target="_blank">3D Massing</a
                >
            </li>
            <li>
                <a
                    href="https://open.toronto.ca/dataset/property-boundaries/"
                    target="_blank">Property Boundaries</a
                >
            </li>
            <li><a href="/static/toronto_far.csv">FAR Data</a></li>
        </ul>

        <p>
            Explore the project on
            <a
                href="https://github.com/schoolofcities/floor-area-ratio"
                target="_blank"
            >
                GitHub
            </a>.<img
                src="src/assets/github-mark.svg"
                alt="GitHub Logo"
                style=" height: 15px; vertical-align: center; padding: 0 3px;"
            />
        </p>

        <p>
            Map attributions: <br /><a
                target="_blank"
                href="https://openstreetmap.org">OpenStreetMap</a
            >, <br /><a target="_blank" href="https://open.toronto.ca/"
                >City of Toronto</a
            >
        </p>
    </div>

    <div class="bottom-content">
        <button
            class="btn toggle-text-btn"
            on:click={toggleTextVisibility}
            style="margin-bottom: 10px; font-size: 12px;"
        >
            {isTextVisible ? "▼" : "▲"}
        </button>

        <div id="legend">
            <div
                id="legend-title"
                style="text-align: center; font-size: 14px; margin-bottom: 5px;"
            >
                Floor Area Ratio (FAR)
            </div>
            <svg xmlns="http://www.w3.org/2000/svg" width="250" height="50">
                <rect x="0%" y="10" width="20%" height="15" fill="#c8d1e5" />
                <rect x="20%" y="10" width="20%" height="15" fill="#89b6d6" />
                <rect x="40%" y="10" width="20%" height="15" fill="#499fb9" />
                <rect x="60%" y="10" width="20%" height="15" fill="#17898c" />
                <rect x="80%" y="10" width="20%" height="15" fill="#015847" />
                <text x="0%" y="45" font-size="12">0.1</text>
                <text x="20%" y="45" font-size="12">1.0</text>
                <text x="40%" y="45" font-size="12">2.0</text>
                <text x="60%" y="45" font-size="12">5.0</text>
                <text x="80%" y="45" font-size="12">15.0+</text>
            </svg>
        </div>

        <a href="https://schoolofcities.utoronto.ca/" target="_blank">
            <img class="logo" src="src/assets/top-logo-full.svg" alt="Logo" />
        </a>
    </div>
</div>

<button
    class="btn toggle-3d-btn {is3DVisible ? 'active' : ''}"
    on:click={toggle3DVisibility}
    style="margin-top: 10px;"
>
    {is3DVisible ? "3D" : "3D"}
</button>

<div id="map"></div>

<style>
    #legend-title {
        font-family: TradeGothicBold;
    }

    .btn.toggle-3d-btn {
        position: fixed;
        top: 95px;
        right: 8px;
        width: 32px;
        font-size: 10pt;
        background-color: white;
        padding: 5px;
        border-radius: 5px;
        border: 2px solid rgb(228, 228, 228);
        cursor: pointer;
        font-weight: regular;
    }

    .btn.toggle-3d-btn.active {
        background-color: #e0e0e0;
    }

    a:hover .logo {
        opacity: 0.7;
    }

    #map {
        position: absolute;
        width: 100%;
        height: 100%;
        z-index: -1;
    }

    #box {
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        padding: 1rem;
        box-sizing: border-box;
        position: absolute;
        margin: 15px;
        padding: 20px;
        width: 350px;
        border-radius: 0.8em;
        background-color: rgba(255, 255, 255, 0.9);
        border: 1px solid #ccc;
        overflow: hidden;
        bottom: 0;
    }

    .title {
        margin: 0 0 5px 0;
        align-self: center;
        font-family: TradeGothicBold;
    }

    .text {
        flex-grow: 1;
        overflow-y: auto;
        font-family: SourceSerif;
    }

    h3 {
        margin: 0;
    }

    .toggle-text-btn {
        background-color: rgba(0, 0, 0, 0);
        color: black;
        padding: 5px 0 0 0;
        width: 100%;
        border: 0px solid #ccc;
        cursor: pointer;
        /* border-bottom: #ccc 1px solid; */
        border-top: #ccc 1px solid;
        font-size: 12pt;
    }

    .toggle-3d-btn {
        background-color: white;
        color: black;
        padding: 5px;
        width: 150px;
        border-radius: 5px;
        border: 1px solid #ccc;
        cursor: pointer;
        margin: 0 0;
    }

    #legend {
        margin: 0 10px;
        width: 250px;
    }

    .logo {
        width: 250px;
        margin-top: 10px;
    }

    .far-diagram {
        width: 150px;
        height: auto;
    }

    .bottom-content {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .equation {
        display: flex;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 10px 0;
        
    }

 mi {
    font-size: 15px;
    font-style: italic;
    padding: 5px;
 }

    @media screen and (max-width: 750px) {
        #box {
            position: absolute;
            bottom: 0;
            width: calc(100% - 30px);
            z-index: 1;
        }

        .text {
            flex-grow: 1;
            overflow-y: auto;
        }

        .far-diagram {
            width: 200px;
        }
    }
</style>
