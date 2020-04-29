
/**
 * Try to render all Latex Math in the ANKI card
 * @throws Error if window.renderMathInElement wasn't found!
 */
function renderMethodMdTableToAnkiDeck() {
    console.info("Md2Anki - renderMethodMdTableToAnkiDeck()");
    if (window.renderMathInElement !== null) {
        console.info("Md2Anki - renderMethodMdTableToAnkiDeck() window.renderMathInElement() was found");
        renderMathInElement(document.querySelector('.card'), {
            delimiters: [{
                left: "$$",
                right: "$$",
                display: true
            }, {
                left: "$",
                right: "$",
                display: false
            }]
        });
    } else {
        throw Error("Md2Anki Error - Katex renderMathInElement() was not found!");
    }
}

/**
 * Get the necessary scripts
 * @param callback {function} Gets called when scripts are loaded
 */
function getScripts(callback) {
    console.info("Md2Anki - getScripts()");
    const katexVersion = '0.11.1'
    const katexBasePath = `https://cdn.jsdelivr.net/npm/katex@${katexVersion}/dist/`
    const katexSrc = `${katexBasePath}katex.min.js`
    const katexAutoRendererSrc = `${katexBasePath}contrib/auto-render.min.js`

    const script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = katexSrc;
    document.body.appendChild(script);
    script.addEventListener('load', () => {
        console.info(`script ${script.src} was loaded`);
        const script2 = document.createElement('script');
        script2.type = 'text/javascript';
        script2.src = katexAutoRendererSrc;
        document.body.appendChild(script2);
        script2.addEventListener('load', () => {
            console.info(`script ${script2.src} was loaded`);
            callback();
        });
    });
}

try {
    if (window.renderMathInElement !== null) {
        // If the necessary render method exists run it
        console.info("Md2Anki - Katex renderMathInElement() was found, execute renderer");
        renderMethodMdTableToAnkiDeck();
    } else {
        // Else get the scripts and run it then
        console.info("Md2Anki - Katex renderMathInElement() wasn't found, get scripts");
        getScripts(() => {
            console.info("Md2Anki - Katex scripts loaded, execute renderer");
            renderMethodMdTableToAnkiDeck();
        })
    }
} catch (e) {
    console.error(e);
    // If any error comes up get the scripts and run it then
    console.info("Md2Anki Error get scripts and then render");
    getScripts(() => {
        console.info("Md2Anki - Katex scripts loaded, execute renderer");
        renderMethodMdTableToAnkiDeck();
    })
}
