const fs = require('fs');

const wasmFilePath = process.argv[2];
if (!wasmFilePath) {
    console.error("Por favor, proporciona la ruta al archivo .wasm");
    process.exit(1);
}

// Objeto de importación que Wasm espera.
// Contiene las funciones que el código Wasm puede llamar.
const importObject = {
  env: {
    // Función para abortar la ejecución en caso de error.
    abort: (errorCode) => {
      let message = "Error desconocido en Wasm.";
      if (errorCode === 1) {
        message = "Error en tiempo de ejecucion: Division por cero.";
      } else if (errorCode === 2) {
        message = "Error en tiempo de ejecucion: Overflow en suma de enteros.";
      } else if (errorCode === 3) {
        message = "Error en tiempo de ejecucion: Recursion detectada. Una funcion no puede invocarse a si misma.";
      }
      // Puedes añadir más códigos de error aquí.
      console.error(`\n--- ABORT ---`);
      console.error(message);
      console.error(`-------------`);
      process.exit(errorCode); // Termina el programa Node.js con un código de error.
    },
    // Funciones para implementar la sentencia PRINT.
    console_log_i32: (value) => {
      console.log(value);
    },
    console_log_f64: (value) => {
      console.log(value);
    }
  }
};

const wasmBuffer = fs.readFileSync(wasmFilePath);

WebAssembly.instantiate(wasmBuffer, importObject).then(wasmModule => {
    const { main } = wasmModule.instance.exports;
    if (main) {
        const result = main();
        console.log(`\nEl programa finalizo con codigo de salida: ${result}`);
    } else {
        console.error("La funcion 'main' no fue encontrada en el modulo wasm.");
    }
}).catch(err => {
    console.error("Error al instanciar el modulo wasm:", err);
});