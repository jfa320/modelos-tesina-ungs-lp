import os

class TraceFileGenerator:
    def __init__(self, filename):
        self.filename = filename

    def write_trace_record(self, input_file_name, solver_name, model_status, solver_status, objective_value, solver_time):
            # Crear la carpeta 'RESULTADOS' solo cuando se llama a este método
            directory = "Resultados"
            if not os.path.exists(directory):
                os.makedirs(directory)
            
            # Guardar el archivo dentro de la carpeta 'RESULTADOS'
            full_path = os.path.join(directory, self.filename)

            with open(full_path, 'a') as file:
                # Escribir los encabezados si el archivo está vacío
                if file.tell() == 0:
                    file.write("* Trace Record Definition\n")
                    file.write("* InputFileName,SolverName,ModelStatus,SolverStatus,ObjectiveValue,SolverTime\n")
                
                # Escribir los datos
                file.write(f"{input_file_name},{solver_name},{model_status},{solver_status},{objective_value},{solver_time}\n")


