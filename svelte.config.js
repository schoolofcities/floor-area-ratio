// import adapter from '@sveltejs/adapter-auto';
import adapter from "@sveltejs/adapter-static"; 
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
// import preprocess from 'svelte-preprocess';

const dev = "production" === "development";

const config = {

	preprocess: vitePreprocess(),

	kit: {
		adapter: adapter({
		    pages: "docs",
		    assets: "docs"
		}),
		paths: {
		    // change below to your repo name
		    base: dev ? "" : "/floor-area-ratio",
		}
	}
};

export default config;