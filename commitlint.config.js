module.exports = {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "body-max-line-length": [0, "always", Infinity],
    "header-max-length": [1, "always", 80],
    "header-case": [2, "always", "lower-case"],
    "type-case": [2, "always", "lower-case"],
  },
};
