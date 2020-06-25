module.exports = {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "body-max-line-length": [0, "always", Infinity],
    "header-case": [2, "always", "lower-case"],
    "type-case": [2, "always", "lower-case"],
  },
};
