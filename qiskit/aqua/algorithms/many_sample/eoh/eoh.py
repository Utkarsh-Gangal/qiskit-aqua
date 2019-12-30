# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2018, 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""
The Quantum Dynamics algorithm.
"""

import logging

from qiskit import QuantumRegister
from qiskit.aqua import AquaError
from qiskit.aqua.algorithms import QuantumAlgorithm
from qiskit.aqua.operators import op_converter
from qiskit.aqua.operators import BaseOperator
from qiskit.aqua.components.initial_states import InitialState

logger = logging.getLogger(__name__)


class EOH(QuantumAlgorithm):
    """
    The Quantum EOH (Evolution of Hamiltonian) algorithm.
    """

    def __init__(self, operator: BaseOperator,
                 initial_state: InitialState,
                 evo_operator: BaseOperator,
                 evo_time: int = 1, num_time_slices: int = 1,
                 expansion_mode: str = 'trotter',
                 expansion_order: int = 1) -> None:
        self._validate_eoh(evo_time, num_time_slices, expansion_mode, expansion_order)
        super().__init__()
        self._operator = op_converter.to_weighted_pauli_operator(operator)
        self._initial_state = initial_state
        self._evo_operator = op_converter.to_weighted_pauli_operator(evo_operator)
        self._evo_time = evo_time
        self._num_time_slices = num_time_slices
        self._expansion_mode = expansion_mode
        self._expansion_order = expansion_order
        self._ret = {}

    def _validate_eoh(self, evo_time: int, num_time_slices: int,
                      expansion_mode: str, expansion_order: int) -> None:
        if evo_time < 0:
            raise AquaError('Evo time value {}. Minimum value allowed is 0'.format(evo_time))
        if num_time_slices < 0:
            raise AquaError(
                'Num time slices value {}. Minimum value allowed is 0'.format(num_time_slices))
        if expansion_mode not in ['trotter', 'suzuki']:
            raise AquaError(
                "Expansion Mode value '{}'. Values allowed are 'trotter', 'suzuki'".format(
                    expansion_mode))
        if expansion_order < 1:
            raise AquaError(
                'Expansion order value {}. Minimum value allowed is 1'.format(expansion_order))

    def construct_circuit(self):
        """
        Construct the circuit.

        Returns:
            QuantumCircuit: the circuit.
        """
        quantum_registers = QuantumRegister(self._operator.num_qubits, name='q')
        qc = self._initial_state.construct_circuit('circuit', quantum_registers)

        qc += self._evo_operator.evolve(
            evo_time=self._evo_time,
            num_time_slices=self._num_time_slices,
            quantum_registers=quantum_registers,
            expansion_mode=self._expansion_mode,
            expansion_order=self._expansion_order,
        )

        return qc

    def _run(self):
        qc = self.construct_circuit()
        qc_with_op = self._operator.construct_evaluation_circuit(
            wave_function=qc, statevector_mode=self._quantum_instance.is_statevector)
        result = self._quantum_instance.execute(qc_with_op)
        self._ret['avg'], self._ret['std_dev'] = self._operator.evaluate_with_result(
            result=result, statevector_mode=self._quantum_instance.is_statevector)
        return self._ret
