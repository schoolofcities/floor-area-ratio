<script>
    import { onMount } from "svelte";
    import maplibregl from "maplibre-gl";
    import "../assets/styles.css";
    import "maplibre-gl/dist/maplibre-gl.css";

    import * as pmtiles from "pmtiles";
    import BaseLayer from "../data/toronto.json";

    let MASSING_URL = "MASSING_FAR.pmtiles";
    let FAR_DATA_URL = "FAR-DATA.pmtiles";
    let FAR_PROPERTY_URL = "FAR-PROPERTY.pmtiles";

    let map;
    let is3DVisible = false;

    const scale = new maplibregl.ScaleControl({
        maxWidth: 100,
        unit: "metric",
    });

    const attributionString = [
        '<a href="https://openstreetmap.org">OpenStreetMap</a>',
        '<a href="https://open.toronto.ca/">City of Toronto</a>',
    ].join(", ");

    const toggle3DVisibility = () => {
        is3DVisible = !is3DVisible;
        if (map.getLayer("massing-layer")) {
            map.setLayoutProperty(
                "massing-layer",
                "visibility",
                is3DVisible ? "visible" : "none",
            );
        }
    };

    let isTextVisible = true;
    const toggleTextVisibility = () => {
        isTextVisible = !isTextVisible;
    };

    onMount(async () => {
        const protocol = new pmtiles.Protocol();
        maplibregl.addProtocol("pmtiles", protocol.tile);

        map = new maplibregl.Map({
            container: "map",
            style: {
                version: 8,
                name: "Empty",
                glyphs: "https://schoolofcities.github.io/fonts/fonts/{fontstack}/{range}.pbf",
                sources: {},
                layers: [
                    {
                        id: "background",
                        type: "background",
                        paint: { "background-color": "rgba(0,0,0,0)" },
                    },
                ],
            },
            center: [-79.409168, 43.650783],
            zoom: 11.6,
            bearing: -17,
            scrollZoom: true,
            minZoom: 10.5,
            // maxPitch: 0,
            maxBounds: [
                [-79.8, 43.35],
                [-79.0, 43.9],
            ],
            attributionControl: false,
        });

        //MAP INTERACTIONS
        map.boxZoom.disable();

        if (window.innerWidth >= 750) {
            map.addControl(scale, "bottom-right");
        }

        //RESIZE EVENTS
        window.addEventListener("resize", () => {
            // MOVE SCALE BAR
            if (window.innerWidth < 750 && map.hasControl(scale)) {
                map.removeControl(scale); // Remove the scale bar if screen width is less than 750px
            } else if (window.innerWidth >= 750 && !map.hasControl(scale)) {
                map.addControl(scale, "bottom-right"); // Add the scale bar back if screen width is 750px or more
            }

            // TEXT
            if (window.innerWidth >= 750) {
                isTextVisible = true;
            }
            if (window.innerWidth < 750) {
                isTextVisible = false;
            }
        });
        map.addControl(
            new maplibregl.NavigationControl({
                showCompass: true,
                visualizePitch: true,
            }),
            "top-right",
        );

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
                    center: [-79.374801, 43.641761],
                    zoom: 11.6,
                    bearing: -17,
                });
            }

            //BASE MAP
            map.addSource("protomaps", {
                type: "vector",
                url: "pmtiles://toronto.pmtiles",
                attribution: attributionString,
            });

            BaseLayer.forEach((layer) => map.addLayer(layer));

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
                        ["<", ["get", "far"], 0.5],
                        "#f6eff7",
                        ["<", ["get", "far"], 1.0],
                        "#bdc9e1",
                        ["<", ["get", "far"], 2.0],
                        "#67a9cf",
                        ["<", ["get", "far"], 5.0],
                        "#1c9099",
                        "#016c59",
                    ],
                    "fill-opacity": 1,
                },
            });

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
                        ["<", ["get", "far"], 0.5],
                        "#f6eff7",
                        ["<", ["get", "far"], 1.0],
                        "#bdc9e1",
                        ["<", ["get", "far"], 2.0],
                        "#67a9cf",
                        ["<", ["get", "far"], 5.0],
                        "#1c9099",
                        "#016c59",
                    ],
                    "fill-extrusion-height": ["get", "AVG_HEIGHT"],
                    "fill-extrusion-base": 0,
                    "fill-extrusion-opacity": 0.9,
                },
                layout: {
                    visibility: "none",
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

            //MOVING LABELS TO THE TOP
            map.moveLayer("roads_labels_minor");
            map.moveLayer("roads_labels_major");
            map.moveLayer("places_subplace");
            map.moveLayer("pois_important");
            map.moveLayer("places_locality");
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

<div id="box">
    <div class="title">
        <h3>Toronto FAR Map</h3>
    </div>

    <button
        class="btn toggle-text-btn"
        on:click={toggleTextVisibility}
        style="margin-bottom: 10px;"
    >
        {isTextVisible ? "Hide Info" : "Show Info"}
    </button>

    <div class="text" style="display: {isTextVisible ? 'block' : 'none'};">
        <p><strong>What is Floor Area Ratio (FAR)?</strong></p>
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
        <p><em>FAR = Total Building Floor Area ÷ Lot Area</em></p>
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

        <p style="display: flex; flex-direction: column; justify-content: center; align-items: center;">
            <!-- These examples all have the same FAR of 1.0: -->
            <img src="/src/assets/far-a.svg" alt="FAR Diagram" style="max-width: 150px; height: auto;" /> <small>FAR: 1.0</small>
            <img src="/src/assets/far-b.svg" alt="FAR Diagram" style="max-width: 150px; height: auto;" /> <small>FAR: 1.0</small>
            <img src="/src/assets/far-c.svg" alt="FAR Diagram" style="max-width: 150px; height: auto;" /><small>FAR: 1.0</small>
        </p>
        <p></p>
        <p><strong>Methodology</strong></p>
        <p>
            This visualization was created using 3D massing and property line
            data from
            <a href="https://open.toronto.ca/" target="_blank"
                >the City of Toronto’s Open Data Portal</a
            >. For the FAR calculations, we assumed an average building floor
            height of 3 meters.
        </p>
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
            Download the FAR data as a GeoJSON file <a href="#">here</a>.
        </p>

        <small>
            Map attributions: <br /><a
                target="_blank"
                href="https://openstreetmap.org">OpenStreetMap</a
            >, <br /><a target="_blank" href="https://open.toronto.ca/"
                >City of Toronto</a
            >
        </small>
    </div>

    <div id="legend">
        <svg xmlns="http://www.w3.org/2000/svg" width="250" height="50">
            <!-- <text x="0" y="20" font-size="16" font-weight="bold" 
                >Floor Area Ratio (FAR)</text
            > -->
            <rect x="0%" y="10" width="20%" height="15" fill="#f6eff7" />
            <rect x="20%" y="10" width="20%" height="15" fill="#bdc9e1" />
            <rect x="40%" y="10" width="20%" height="15" fill="#67a9cf" />
            <rect x="60%" y="10" width="20%" height="15" fill="#1c9099" />
            <rect x="80%" y="10" width="20%" height="15" fill="#016c59" />
            <text x="0%" y="45" font-size="12">0</text>
            <text x="20%" y="45" font-size="12">0.5</text>
            <text x="40%" y="45" font-size="12">1.0</text>
            <text x="60%" y="45" font-size="12">2.0</text>
            <text x="80%" y="45" font-size="12">5.0 +</text>
        </svg>
    </div>
    <button
        class="btn toggle-3d-btn"
        on:click={toggle3DVisibility}
        style="margin-top: 10px;"
    >
        {is3DVisible ? "Hide 3D Buildings" : "Show 3D Buildings"}
    </button>

    <div class="bottom-content">
        <a href="https://schoolofcities.utoronto.ca/" target="_blank">
            <img class="logo" src="src/assets/top-logo-full.svg" alt="Logo" />
        </a>
    </div>
</div>

<div id="map"></div>

<style>
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
        height: calc(100vh - 40px);
        padding: 1rem;
        box-sizing: border-box;

        position: absolute;
        margin: 20px;
        padding: 20px;
        width: 300px;
        border-radius: 0.8em;
        background-color: rgba(255, 255, 255, 0.9);
        border: 1px solid #ccc;
        overflow: hidden;
    }

    .title {
        margin: 0 0 0 0;
    }

    .text {
        flex-grow: 1;
        overflow-y: auto;
    }

    h3 {
        margin: 0;
    }

    .bottom-content {
        display: flex;
        flex-direction: column;
    }

    .toggle-text-btn {
        background-color: white;
        color: black;
        padding: 5px;
        width: 150px;
        border-radius: 5px;
        border: 1px solid #ccc;
        cursor: pointer;
    }

    .toggle-3d-btn {
        background-color: white;
        color: black;
        padding: 5px;
        width: 150px;
        border-radius: 5px;
        border: 1px solid #ccc;
        cursor: pointer;
    }

    #legend {
        margin: 10px;
    }

    .logo {
        width: 250px;
        margin-top: 20px;
    }

    @media screen and (min-width: 750px) {
        .toggle-text-btn {
            display: none; /* Hide the button on larger screens */
        }
    }

    @media screen and (max-width: 750px) {
        #box {
            position: absolute;
            bottom: 0;
            height: 40vh;
            left: 0;
            width: calc(100vw - 40px);
            /* height: 300px; */
            margin: 20px;
            padding: 20px;
            overflow: hidden;
        }

        .text {
            max-height: 15vh;
        }

        .logo {
            max-width: 250px;
            width: 50vw;
        }

        .bottom-content {
            /* display: flex;
            flex-direction: column;
            position: absolute;
            bottom: 20px; */
        }

        .toggle-text-btn {
            position: fixed;
            bottom: 90px;
            right: 40px;
            width: 30vw;
            font-size: 9pt;
        }

        .toggle-3d-btn {
            position: fixed;
            bottom: 45px;
            right: 40px;
            width: 30vw;
            font-size: 9pt;
        }
    }
</style>
