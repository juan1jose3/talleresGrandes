<?php 
// ----------------------------------------------------
// CRUD DE ARREGLOS EN PHP USANDO SESIONES
// ----------------------------------------------------
// Este programa permite Crear, Leer, Actualizar y 
// Eliminar elementos dentro de un arreglo almacenado
// en la sesión del usuario.
// ----------------------------------------------------

session_start(); // Iniciamos la sesión para guardar el arreglo y mantener los datos

// --------------------- CREACIÓN DEL ARREGLO ---------------------

// Si todavía no existe un arreglo en la sesión, lo inicializamos como vacío
if (!isset($_SESSION['arreglo'])) {
    $_SESSION['arreglo'] = []; 
}

// --------------------- C (CREATE) ---------------------

// Verificamos si el usuario envió un valor nuevo desde el formulario
if (isset($_POST['valor']) && $_POST['valor'] != "") {
    $_SESSION['arreglo'][] = $_POST['valor']; // Agregamos el valor al arreglo en la última posición
}

// --------------------- R (READ / RESET) ---------------------

// Si se presionó el botón "Reiniciar", borramos el arreglo
if (isset($_POST['reiniciar'])) {
    $_SESSION['arreglo'] = []; // Se vacía el arreglo
}

// --------------------- U (UPDATE) ---------------------

// Si el formulario envía un índice y un nuevo valor
if (isset($_POST['indice']) && isset($_POST['nuevo_valor'])) {
    $indice = intval($_POST['indice']); // Convertimos a número el índice
    $nuevo_valor = $_POST['nuevo_valor']; // Guardamos el nuevo valor enviado

    // Validamos que el índice exista dentro del arreglo
    if (isset($_SESSION['arreglo'][$indice])) {
        $_SESSION['arreglo'][$indice] = $nuevo_valor; // Reemplazamos el valor viejo por el nuevo
        $mensaje = "Valor en el índice $indice actualizado correctamente.";
    } else {
        $mensaje = "El índice $indice no existe en el arreglo.";
    }
}

// --------------------- D (DELETE) ---------------------

// Si el usuario pidió eliminar un índice
if (isset($_POST['eliminar_indice'])) {
    $indice = intval($_POST['eliminar_indice']); // Convertimos a número el índice
    if (isset($_SESSION['arreglo'][$indice])) {
        unset($_SESSION['arreglo'][$indice]); // Eliminamos el valor del arreglo
        $_SESSION['arreglo'] = array_values($_SESSION['arreglo']); // Reindexamos para no dejar huecos
        $mensaje = "Valor en el índice $indice eliminado correctamente.";
    } else {
        $mensaje = "El índice $indice no existe en el arreglo.";
    }
}
?>

<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>CRUD de Arreglos en PHP</title>
    <style>
        /* Estilos básicos para que se vea ordenado */
        body { font-family: Arial, sans-serif; background: #f4f4f9; padding: 20px; }
        h2 { color: #333; }
        form { margin-bottom: 15px; background: #fff; padding: 10px; border-radius: 5px; }
        input[type="text"], input[type="number"] { padding: 8px; margin: 5px; }
        button { padding: 8px 12px; margin: 5px; cursor: pointer; }
        .resultado { background: #fff; padding: 10px; border-radius: 5px; margin-top: 10px; }
        .mensaje { margin: 10px 0; padding: 8px; border-radius: 5px; background: #eef; }
    </style>
</head>
<body>

    <!-- TÍTULO DE LA PÁGINA -->
    <h2>CRUD de Arreglos en PHP</h2>

    <!-- FORMULARIO CREATE -->
    <!-- Permite agregar un valor nuevo al arreglo -->
    <form method="post">
        <h3>Agregar valor</h3>
        <input type="text" name="valor" placeholder="Nuevo valor" required>
        <button type="submit">Agregar</button>
    </form>

    <!-- FORMULARIO READ/RESET -->
    <!-- Botón para mostrar el arreglo y otro para reiniciarlo -->
    <form method="post">
        <button type="submit" name="mostrar">Mostrar Arreglo</button>
        <button type="submit" name="reiniciar">Reiniciar Arreglo</button>
    </form>

    <!-- FORMULARIO UPDATE -->
    <!-- Permite editar un valor existente en una posición específica -->
    <form method="post">
        <h3>Editar valor</h3>
        <label>Índice : </label>
        <input type="number" name="indice" min="0" required>
        <label>Nuevo valor : </label>
        <input type="text" name="nuevo_valor" required>
        <button type="submit">Editar</button>
    </form>

    <!-- FORMULARIO DELETE -->
    <!-- Permite eliminar un valor del arreglo según el índice -->
    <form method="post">
        <h3>Eliminar valor</h3>
        <label>Índice : </label>
        <input type="number" name="eliminar_indice" min="0" required>
        <button type="submit">Eliminar</button>
    </form>

    <!-- MENSAJES DE ÉXITO O ERROR -->
    <?php if (!empty($mensaje)) { ?>
        <div class="mensaje"><?php echo $mensaje; ?></div>
    <?php } ?>

    <!-- RESULTADO DEL ARREGLO -->
    <!-- Se imprime el contenido actual del arreglo -->
    <div class="resultado">
        <h3>Contenido actual del arreglo:</h3>
        <?php
        if (!empty($_SESSION['arreglo'])) {
            echo "<ul>";
            // Recorremos el arreglo e imprimimos índice y valor
            foreach ($_SESSION['arreglo'] as $indice => $valor) {
                echo "<li>Índice $indice => $valor</li>";
            }
            echo "</ul>";
        } else {
            // Si está vacío mostramos un mensaje
            echo "<p><em>El arreglo está vacío</em></p>";
        }
        ?>
    </div>

</body>
</html>
