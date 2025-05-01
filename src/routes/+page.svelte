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

    import farA from "../assets/far-a.svg";
    import farB from "../assets/far-b.svg";
    import farC from "../assets/far-c.svg";
    import socLogo from "../assets/top-logo-full.svg";
    import githubLogo from "../assets/github-mark.svg";

    let map;
    let is3DVisible = false;

    // const colourGradient = ["#EBF7F7","#69C8BA","#00A189","#077869", "#0D534D"];
    // const colourGradient = ["#c8d1e5","#89b6d6","#499fb9","#17898c","#015847"];
    // const colourGradient = ["#C5E3E7","#84CEE9","#33A0C4","#056F83","#0D534D"];
    // const colourGradient = ["#D4E7E8","#97C9D4","#47A2BA","#007FA3","#0D534D"];
    const colourGradient = ["#c8d1e5","#89b6d6","#499fb9","#007FA3","#0D534D"];

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
                duration: 750,
            });
            map.dragRotate.enable();
            map.dragRotate.setPitchWithRotate(true);
            map.touchZoomRotate.enableRotation();
        } else {
            map.easeTo({
                pitch: 0,
                duration: 750,
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
            center: [-79.3961, 43.6530],
            zoom: 13,
            bearing: -17,
            // pitch: 10,
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
                        colourGradient[0], // 0.1 - 1.0
                        ["<", ["get", "far"], 2.0],
                        colourGradient[1], // 1.0 - 2.0
                        ["<", ["get", "far"], 5.0],
                        colourGradient[2], // 2.0 - 5.0
                        ["<", ["get", "far"], 15.0],
                        colourGradient[3], // 5.0 - 15.0
                        colourGradient[4], // > 15.0
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
                        colourGradient[0], // 0.1 - 1.0
                        ["<=", ["get", "far"], 2.0],
                        colourGradient[1], // 1.0 - 2.0
                        ["<=", ["get", "far"], 5.0],
                        colourGradient[2], // 2.0 - 5.0
                        ["<=", ["get", "far"], 15.0],
                        colourGradient[3], // 5.0 - 15.0
                        colourGradient[4], // > 15.0
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



<div
    id="box"
    style="height: {isTextVisible ? 'calc(100dvh - 30px)' : '250px'}; "
>
    <div class="title">
        <h3>Toronto FAR Map</h3>
    </div>

    <div class="text" style="display: {isTextVisible ? 'block' : 'none'};">
        <h4>What is Floor Area Ratio (FAR)?</h4>
        <p>
           
            <a
                href="https://www.linkedin.com/in/scott-christian-mccallum/"
                target="_blank">Scott McCallum</a
            >,  <a href="https://jamaps.github.io/" target="_blank">Jeff Allen</a> | April 2025
        </p>
        <p>
            FAR is a measure of urban built density, measured as a building's total floor area relative to the
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
            suggest less built-up land use.
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
            <img class="far-diagram" src={farC} alt="FAR Diagram" />
            FAR: 1.0
            <img class="far-diagram" src={farB} alt="FAR Diagram" />
            FAR: 1.0
            <img class="far-diagram" src={farA} alt="FAR Diagram" />
            FAR: 1.0
        </p>
        <p></p>
        <h4>Methodology</h4>
        <p>
            This visualization was created combining 3D massing and property
            boundary data from
            <a href="https://open.toronto.ca/" target="_blank"
                >the City of Toronto’s Open Data Portal</a
            >. For the FAR calculations, we assumed an average building floor
            height of 3 meters.
        </p>

        <h4>Data download links</h4>
        <ul>
            <li>
                <a href="./toronto_far.csv">FAR Data</a>
            </li>
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
            
        </ul>

        <p>
            Explore the project on
            <a
                href="https://github.com/schoolofcities/floor-area-ratio"
                target="_blank"
            >
                GitHub
            </a>.<img
                src={githubLogo}
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
        <div class="button-container">
            <button
                class="btn toggle-text-btn"
                on:click={toggleTextVisibility}
            >
                {isTextVisible ? "▼ Hide Info" : "▲ Show Info "}
            </button>
            <button
                class="btn toggle-3d-btn {is3DVisible ? 'active' : ''}"
                on:click={toggle3DVisibility}
            >
                {is3DVisible ? "3D" : "3D"}
            </button>
        </div>

        <div id="legend">
            <div
                id="legend-title"
                style="text-align: center; font-size: 14px; margin-bottom: 5px;"
            >
                Floor Area Ratio (FAR)
            </div>
            <svg xmlns="http://www.w3.org/2000/svg" width="250" height="50">
                <rect x="0%" y="10" width="20%" height="15" fill={colourGradient[0]} />
                <rect x="20%" y="10" width="20%" height="15" fill={colourGradient[1]} />
                <rect x="40%" y="10" width="20%" height="15" fill={colourGradient[2]} />
                <rect x="60%" y="10" width="20%" height="15" fill={colourGradient[3]} />
                <rect x="80%" y="10" width="20%" height="15" fill={colourGradient[4]} />
                <text x="0%" y="45" font-size="12">0.1</text>
                <text x="20%" y="45" font-size="12">1.0</text>
                <text x="40%" y="45" font-size="12">2.0</text>
                <text x="60%" y="45" font-size="12">5.0</text>
                <text x="80%" y="45" font-size="12">15.0+</text>
            </svg>
        </div>

        <a href="https://schoolofcities.utoronto.ca/" target="_blank">
            <img class="logo" src={socLogo} alt="Logo" />
        </a>
    </div>
</div>

<div id="map"></div>

<style>

    #legend-title {
        font-family: TradeGothicBold;
    }

    .button-container {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        margin: 10px;
    }


    .btn.toggle-3d-btn.active {
        background-color: #e0e0e0;
    }


    .toggle-text-btn {
        background-color: rgba(0, 0, 0, 0);
        color: black;
        /* margin: 10px 0 0 0; */
        width: 100px;
        height: 25px;
        border: 1px solid #ccc;
        cursor: pointer;
        /* border-bottom: #ccc 1px solid; */
        font-size: 10pt;
        border-radius: 5px;
        font-family: TradeGothicBold;
        /* display: flex;
        justify-content: center;
        align-items: center; */
    }

    .toggle-text-btn:hover {
        background-color: #e0e0e0;
    }

    .toggle-3d-btn {
        background-color: rgba(0, 0, 0, 0);
        color: black;
        /* margin: 10px 0 0 0; */
        width: 35px;
        padding: 0 20px;
        height: 25px;
        border: 1px solid #ccc;
        cursor: pointer;
        /* border-bottom: #ccc 1px solid; */
        font-size: 10pt;
        border-radius: 5px;
        font-family: TradeGothicBold;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .toggle-3d-btn:hover {
        background-color: #e0e0e0;
    }

    a:hover .logo {
        opacity: 0.8;
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
        width: 360px;
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
        margin-left: -10px;
        flex-grow: 1;
        overflow-y: auto;
        font-family: SourceSerif;
    }

    h3 {
        margin: 0;
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
        border-top: #ccc 1px solid;
    }
    .equation {
        display: flex;
        justify-content: left;
        align-items: center;
        text-align: center;
        padding: 10px 0;
        font-family: TradeGothicBold;
    }

    .equation math {
        font-family: TradeGothicBold;
        font-size: 19px;
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
