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
                [-79.8, 43.35], // Southwest corner (longitude, latitude)
    [-79.0, 43.9], // Northeast coordinates
            ],
            attributionControl: false,
        });

        //MAP INTERACTIONS
        map.boxZoom.disable();

        map.addControl(scale, "bottom-right");
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
                    "fill-extrusion-height": ["get", "AVG_HEIGHT"], // Extrusion height
                    "fill-extrusion-base": 0,
                    "fill-extrusion-opacity": 0.9,
                },
                layout: {
                    visibility: "none", // Hide the layer initially
                },
            });

            // FAR DATA
            map.addSource("far-data", {
                type: "vector",
                url: "pmtiles://" + FAR_DATA_URL,
            });
            map.addLayer({
                id: "far-data-layer",
                type: "fill", // Change to fill layer
                source: "far-data",
                "source-layer": "far", // Replace with the correct source layer name if different
                paint: {
                    "fill-color": "#000000", // Black color (not visible due to opacity)
                    "fill-opacity": 0, // Set opacity to 0
                },
            });

            // Add hover interaction
            const popup = new maplibregl.Popup({
                closeButton: false,
                closeOnClick: false,
            });

            map.on("mousemove", "far-data-layer", (e) => {
                // Check the current zoom level
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
                popup.remove(); // Remove popup when the mouse leaves the layer
            });
        });
    });
</script>

<svelte:head>
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1, minimum-scale=1"
    />
</svelte:head>

<div id="box">
    <div class="title">
        <h3>Toronto FAR Map</h3>
        <p>
            <a href="https://jamaps.github.io/" target="_blank">Jeff Allen</a>,
            <a
                href="https://www.linkedin.com/in/scott-christian-mccallum/"
                target="_blank">Scott McCallum</a
            >
        </p>
    </div>
    <div class="text">
        <p><strong>What is Floor Area Ratio (FAR)?</strong></p>
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
            while maintaining the same FAR.
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

    <button class="btn" on:click={toggle3DVisibility} style="margin-top: 10px;">
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
        opacity: 0.7; /* Adjust the opacity value as needed */
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
        background-color: rgba(255, 255, 255, 0.8);
        border: 1px solid #ccc;
        overflow: hidden;
    }

    .title {
        margin: 0 0 0 0;
    }

    .text {
        flex-grow: 1;
        overflow-y: auto; /* Adds scroll if content overflows */
    }

    h3 {
        margin: 0;
    }

    .bottom-content {
        display: flex;
        flex-direction: column;
    }

    .btn {
        background-color: white;
        color: black;
        padding: 5px;
        width: 150px;
        border-radius: 5px;
        border: 1px solid #ccc;
        cursor: pointer;
    }

    .logo {
        width: 250px;
        margin-top: 20px;
    }

    /* 📱 Mobile styles */
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

        .btn {
            position: fixed;
            bottom: 45px;
            right: 40px;
            width: 30vw;
            font-size: 9pt;
        }
    }
</style>
