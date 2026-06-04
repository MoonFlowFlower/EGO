const { launchElectron } = require("./launch");

launchElectron(["--smoke"], process.argv.slice(2));
