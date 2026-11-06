from router import create_packet, fragment_IP_packet, parse_packet


def test_fragmentation():
    print("=== TEST DE FRAGMENTACIÓN IP ===")

    msg_largo = b"este es un mensaje largo de prueba para fragmentacion IP"  # 56 bytes
    packet_parsed = {
        "ip": "127.0.0.1",
        "port": 8881,
        "ttl": 10,
        "id": 500,
        "offset": 0,
        "tamaño": len(msg_largo),
        "flag": 0,
        "mensaje": msg_largo,
    }
    pkt_original = create_packet(packet_parsed)
    total_size = len(pkt_original)  # 17 de header + 56 = 73 bytes totales

    print(f"tamaño total del paquete original: {total_size} bytes")

    # -------------------------------------------------------------
    # CASO 1: MTU grande (No requiere fragmentación)
    # MTU = 100 (73 <= 100 -> debe retornar 1 solo paquete)
    # -------------------------------------------------------------
    frags_caso1 = fragment_IP_packet(pkt_original, MTU=100)
    print("\n--- MTU 100 ---")
    print(
        f"largo lista de fragmentos: {len(frags_caso1)} (esperado: 1)"
    )
    assert len(frags_caso1) == 1

    # -------------------------------------------------------------
    # CASO 2: MTU pequeño (Requiere fragmentación)
    # MTU = 37 -> max_msg = 37 - 17 = 20 bytes de payload por fragmento
    # 56 bytes / 20 = 3 fragmentos (20 + 20 + 16)
    # -------------------------------------------------------------
    frags_caso2 = fragment_IP_packet(pkt_original, MTU=37)
    print("\n--- MTU 37 ---")
    print(
        f"largo lista de fragmentos: {len(frags_caso2)} (esperado: 3)"
    )

    # Imprimir detalle de cada fragmento generado
    for idx, f_bytes in enumerate(frags_caso2):
        parsed_f = parse_packet(f_bytes)
        print(
            f" fragmento {idx+1}: "
            f"largo total={len(f_bytes)}B (<=37) | "
            f"offset={parsed_f['offset']} | "
            f"tamaño={parsed_f['tamaño']}B | "
            f"FLAG={parsed_f['flag']} | "
            f"mensaje='{parsed_f['mensaje'].decode()}'"
        )  #[cite: 14]

if __name__ == "__main__":
    test_fragmentation()
