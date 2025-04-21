output "hello_output" {
    value = "${var.file_path} has been created with content ${var.file_content}."
    description = "Hello world output"
}
