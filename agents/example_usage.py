"""Example usage of the sales agent system."""

from orchestrator import SalesOrchestrator


def main():
    """Demonstrate the sales agent system."""
    
    # Initialize the orchestrator
    orchestrator = SalesOrchestrator()

    # Example 1: Process a new lead
    print("=" * 60)
    print("EXAMPLE 1: Processing a new lead")
    print("=" * 60)
    
    lead_result = orchestrator.process_lead(
        phone="+1-555-0123",
        email="john.doe@example.com",
        name="John Doe",
        source="web_form"
    )
    
    if lead_result["success"]:
        lead_id = lead_result["lead_id"]
        print(f"✓ Lead created: {lead_id}")
        print(f"  Recommended product: {lead_result['recommended_product']['name']}")
    else:
        print(f"✗ Failed to create lead: {lead_result['error']}")
        return

    # Example 2: Handle incoming call
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Handling incoming call")
    print("=" * 60)
    
    call_result = orchestrator.handle_incoming_call(
        phone="+1-555-0123",
        lead_id=lead_id
    )
    
    if call_result["success"]:
        call_id = call_result["call_id"]
        print(f"✓ Call handled: {call_id}")
        print(f"  Queue position: {call_result['queue_position']}")
    else:
        print(f"✗ Failed to handle call: {call_result['error']}")

    # Example 3: Create a sales deal
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Creating a sales deal")
    print("=" * 60)
    
    deal_result = orchestrator.create_sales_deal(
        lead_id=lead_id,
        product_id="PROFESSIONAL",
        discount_percent=10
    )
    
    if deal_result["success"]:
        deal_id = deal_result["deal_id"]
        deal = deal_result["deal"]
        print(f"✓ Deal created: {deal_id}")
        print(f"  Product: {deal['product_name']}")
        print(f"  List price: ${deal['list_price']:.2f}")
        print(f"  Discount: {deal['discount_percent']}%")
        print(f"  Final price: ${deal['final_price']:.2f}")
    else:
        print(f"✗ Failed to create deal: {deal_result['error']}")
        return

    # Example 4: End the call
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Ending the call")
    print("=" * 60)
    
    end_call_result = orchestrator.end_call(
        call_id=call_id,
        outcome="successful",
        agent_notes="Customer interested in Professional plan, sent proposal"
    )
    
    if end_call_result["success"]:
        print(f"✓ Call ended: {call_id}")
        print(f"  Duration: {end_call_result['duration_seconds']} seconds")
        print(f"  Outcome: {end_call_result['outcome']}")
    else:
        print(f"✗ Failed to end call: {end_call_result['error']}")

    # Example 5: Process payment
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Processing payment")
    print("=" * 60)
    
    payment_result = orchestrator.process_payment(
        lead_id=lead_id,
        deal_id=deal_id,
        amount=float(deal["final_price"]),
        payment_method="credit_card"
    )
    
    if payment_result["success"]:
        print(f"✓ Payment processed successfully")
        payment = payment_result["payment"]
        print(f"  Transaction ID: {payment['transaction_id']}")
        print(f"  Amount: ${payment['amount']:.2f}")
        print(f"  Status: {payment['status']}")
        
        invoice = payment_result["invoice"]
        if invoice.get("success"):
            print(f"  Invoice ID: {invoice['invoice_id']}")
    else:
        print(f"✗ Payment failed: {payment_result['error']}")

    # Example 6: Get lead summary
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Lead Summary")
    print("=" * 60)
    
    summary = orchestrator.get_lead_summary(lead_id)
    
    if summary["success"]:
        lead_info = summary["lead"]
        stats = summary["summary"]
        
        print(f"✓ Lead: {lead_info['name']}")
        print(f"  Email: {lead_info['email']}")
        print(f"  Phone: {lead_info['phone']}")
        print(f"  Status: {lead_info['status']}")
        print(f"\n  Statistics:")
        print(f"  - Lead score: {stats['lead_score']}")
        print(f"  - Interactions: {stats['total_interactions']}")
        print(f"  - Calls: {stats['total_calls']}")
        print(f"  - Deals: {stats['total_deals']}")
    else:
        print(f"✗ Failed to get summary: {summary['error']}")

    # Example 7: System status
    print("\n" + "=" * 60)
    print("EXAMPLE 7: System Status")
    print("=" * 60)
    
    system_status = orchestrator.get_system_status()
    
    print("✓ System Status Report:")
    stats = system_status["statistics"]
    print(f"  Total leads: {stats['total_leads']}")
    print(f"  Total calls: {stats['total_calls']}")
    print(f"  Active calls: {stats['active_calls']}")
    print(f"  Total deals: {stats['total_deals']}")
    print(f"  Total transactions: {stats['total_transactions']}")
    
    print("\n  Agent Status:")
    for agent_name, agent_status in system_status["agents"].items():
        print(f"  - {agent_status['name']}: {agent_status['status']}")
        print(f"    Sessions: {agent_status['sessions']}")
        print(f"    Successes: {agent_status['successes']}")
        print(f"    Errors: {agent_status['errors']}")


if __name__ == "__main__":
    main()
