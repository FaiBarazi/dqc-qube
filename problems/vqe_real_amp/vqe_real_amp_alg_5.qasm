// Benchmark created by MQT Bench on 2025-10-16
// For more info: https://www.cda.cit.tum.de/mqtbench/
// MQT Bench version: 2.0.1
// Qiskit version: 2.1.1
// Output format: qasm3

OPENQASM 3.0;
include "stdgates.inc";
bit[5] meas;
qubit[5] q;
ry(6.006735895579343) q[0];
ry(1.304903297657757) q[1];
ry(5.205272730965009) q[2];
ry(0.9379672423735244) q[3];
ry(3.2220464314480877) q[4];
cx q[3], q[4];
cx q[2], q[3];
cx q[1], q[2];
cx q[0], q[1];
ry(0.8540080589393146) q[0];
ry(4.329343885871547) q[1];
ry(5.288856933750764) q[2];
ry(2.6735518805676657) q[3];
ry(6.012543404956273) q[4];
cx q[3], q[4];
cx q[2], q[3];
cx q[1], q[2];
cx q[0], q[1];
ry(5.185719590928789) q[0];
ry(2.125069481984559) q[1];
ry(3.6176102152986354) q[2];
ry(4.733135208207287) q[3];
ry(5.196847304624584) q[4];
cx q[3], q[4];
cx q[2], q[3];
cx q[1], q[2];
cx q[0], q[1];
ry(5.864966885210837) q[0];
ry(0.9110285368422897) q[1];
ry(4.684618627355123) q[2];
ry(0.8755706304852969) q[3];
ry(5.695888160944528) q[4];
barrier q[0], q[1], q[2], q[3], q[4];
meas[0] = measure q[0];
meas[1] = measure q[1];
meas[2] = measure q[2];
meas[3] = measure q[3];
meas[4] = measure q[4];
