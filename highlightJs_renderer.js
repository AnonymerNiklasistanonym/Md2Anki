/**
 * Try to render all source code in the ANKI card
 * @throws Error if hljs.highlightBlock wasn't found!
 */
function renderMethodMdTableToAnkiDeckSourceCode() {
    console.info("Md2Anki - renderMethodMdTableToAnkiDeckSourceCode()");
    if (window.hljs !== null && hljs.highlightBlock !== null) {
        console.info("Md2Anki - renderMethodMdTableToAnkiDeckSourceCode(): hljs.highlightBlock() was found");
        document.querySelectorAll('.card pre code').forEach((block) => {
            hljs.highlightBlock(block);
        });
    } else {
        throw Error("Md2Anki Error - highlight.js hljs.initHighlightingOnLoad() was not found!");
    }
}

/**
 * Get the necessary scripts
 * @param callback {function} Gets called when scripts are loaded
 */
function getScriptsSourceCode(callback) {
    console.info("MdTableToAnkiDeck > getScriptsSourceCode()");
    const highlightJsVersion = '10.0.1'
    const highlightJsBasePath = `https://cdnjs.cloudflare.com/ajax/libs/highlight.js/${highlightJsVersion}/`
    const highlightJsSrc = `${highlightJsBasePath}highlight.min.js`

    const script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = highlightJsSrc;
    document.body.appendChild(script);
    script.addEventListener('load', () => {
        console.info(`Md2Anki - script ${script.src} was loaded`);
        callback();
    });
}

try {
    if (window.hljs !== null && hljs.highlightBlock !== null) {
        // If the necessary render method exists run it
        console.info("Md2Anki - highlightjs hljs.highlightBlock() was found, execute renderer");
        renderMethodMdTableToAnkiDeckSourceCode();
    } else {
        // Else get the scripts and run it then
        console.info("Md2Anki - highlightjs hljs.highlightBlock() wasn't found, get scripts");
        getScriptsSourceCode(() => {
            console.info("Md2Anki - highlightjs scripts loaded, execute renderer");
            renderMethodMdTableToAnkiDeckSourceCode();
        })
    }
} catch (e) {
    console.error(e);
    // If any error comes up get the scripts and run it then
    console.info("Md2Anki Error - get scripts and then render");
    getScriptsSourceCode(() => {
        console.info("Md2Anki - highlightjs scripts loaded, execute renderer");
        renderMethodMdTableToAnkiDeckSourceCode();
    })
}
