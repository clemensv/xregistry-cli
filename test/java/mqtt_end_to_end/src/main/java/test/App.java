package test;

import java.util.HashSet;
import java.util.concurrent.CompletableFuture;
import contoso.erp.producer.*;
import io.cloudevents.CloudEvent;
import io.cloudevents.core.format.EventFormat;
import io.cloudevents.core.message.Encoding;
import io.cloudevents.core.provider.EventFormatProvider;
import io.cloudevents.experimental.endpoints.PlainEndpointCredential;

/**
 * Hello world!
 *
 */
public class App 
{
    public static void main( String[] args ) throws Exception
    {
        new App().run();
    }

    public void run() throws Exception
    {
        // translate the following to Java 17
        var unmatchedEvents = new HashSet<String>();

        EventFormat formatter = EventFormatProvider.getInstance().resolveFormat("application/cloudevents+json");

        var passwordCredential = new PlainEndpointCredential("test", "password");

        var consumer = contoso.erp.consumer.EventsEventConsumer.createForMqttConsumer(passwordCredential, new EventDispatcher(unmatchedEvents));
        consumer.getEndpoint().startAsync().get(15, java.util.concurrent.TimeUnit.SECONDS);

        var producer = EventsEventProducer.createForMqttProducer(passwordCredential, Encoding.STRUCTURED, formatter);
                
        // we still need a hook to track the message-ids

        var employeedata = new EmployeeData();
        employeedata.setEmployeeId("123");
        employeedata.setEmail("johndoe@example.com");
        employeedata.setDepartment("Sales");
        employeedata.setName("John Doe");
        employeedata.setPosition("Sales Manager");
        producer.sendEmployeeAddedAsync(employeedata).get(2, java.util.concurrent.TimeUnit.SECONDS);

        var productdata = new ProductData();
        productdata.setProductId("123");
        productdata.setName("Widget");
        productdata.setPrice(9.99);
        productdata.setDescription("A widget");
        producer.sendProductAddedAsync(productdata).get(2, java.util.concurrent.TimeUnit.SECONDS);

        var orderdata = new OrderData();
        orderdata.setOrderId("123");
        orderdata.setCustomerId("123");
        producer.sendReservationPlacedAsync(orderdata).get(2, java.util.concurrent.TimeUnit.SECONDS);

        var paymentdata = new PaymentData();
        paymentdata.setOrderId("123");
        paymentdata.setAmount(9.99);
        producer.sendPaymentsReceivedAsync(paymentdata).get(2, java.util.concurrent.TimeUnit.SECONDS);

        var shipmentdata = new ShipmentData();
        shipmentdata.setOrderId("123");
        producer.sendShipmentAcceptedAsync(shipmentdata).get(2, java.util.concurrent.TimeUnit.SECONDS);

        var returndata = new ReturnData();
        returndata.setOrderId("123");
        producer.sendReturnRequestedAsync(returndata).get(2, java.util.concurrent.TimeUnit.SECONDS);

        var cancellationdata = new CancellationData();
        cancellationdata.setOrderId("123");
        producer.sendReservationCancelledAsync(cancellationdata).get(2, java.util.concurrent.TimeUnit.SECONDS);

        var refunddata = new RefundData();
        refunddata.setOrderId("123");
        refunddata.setAmount(9.99);
        producer.sendReservationRefundedAsync(refunddata).get(2, java.util.concurrent.TimeUnit.SECONDS);

        consumer.getEndpoint().stopAsync().get(10, java.util.concurrent.TimeUnit.SECONDS);
        consumer.close();
        producer.getEndpoint().close();

        if (unmatchedEvents.size() != 0)
        {
            // we'll fail loudly if we didn't get all the events we sent
            throw new RuntimeException(
                    String.format("Didn't get all the events we sent. Unmatched events: %d", unmatchedEvents.size()));
        }
        // TODO: There's some cleanup needed in the Java threads created by Paho
        System.exit(0);
    }
    
    class EventDispatcher implements contoso.erp.consumer.IEventsDispatcher {

        private HashSet<String> unmatchedEvents;

        public EventDispatcher(HashSet<String> unmatchedEvents)
        {
            this.unmatchedEvents = unmatchedEvents;
        }

        public CompletableFuture<Void> onReservationPlacedAsync(CloudEvent cloudEvent, contoso.erp.consumer.OrderData data) {
            if (cloudEvent.getId() != null)
                unmatchedEvents.remove(cloudEvent.getId());
            return CompletableFuture.completedFuture(null);
        }

        public CompletableFuture<Void> onPaymentsReceivedAsync(CloudEvent cloudEvent, contoso.erp.consumer.PaymentData data) {
            if (cloudEvent.getId() != null)
                unmatchedEvents.remove(cloudEvent.getId());
            return CompletableFuture.completedFuture(null);
        }

        public CompletableFuture<Void> onShipmentAcceptedAsync(CloudEvent cloudEvent, contoso.erp.consumer.ShipmentData data) {
            if (cloudEvent.getId() != null)
                unmatchedEvents.remove(cloudEvent.getId());
            return CompletableFuture.completedFuture(null);
        }

        public CompletableFuture<Void> onShipmentRejectedAsync(CloudEvent cloudEvent, contoso.erp.consumer.ShipmentData data) {
            if (cloudEvent.getId() != null)
                unmatchedEvents.remove(cloudEvent.getId());
            return CompletableFuture.completedFuture(null);
        }   

        public CompletableFuture<Void> onReturnRequestedAsync(CloudEvent cloudEvent, contoso.erp.consumer.ReturnData data) {
            if (cloudEvent.getId() != null)
                unmatchedEvents.remove(cloudEvent.getId());
            return CompletableFuture.completedFuture(null);
        }

        public CompletableFuture<Void> onReservationCancelledAsync(CloudEvent cloudEvent, contoso.erp.consumer.CancellationData data) {
            if (cloudEvent.getId() != null)
                unmatchedEvents.remove(cloudEvent.getId());
            return CompletableFuture.completedFuture(null);
        }

        public CompletableFuture<Void> onReservationRefundedAsync(CloudEvent cloudEvent, contoso.erp.consumer.RefundData data) {
            if (cloudEvent.getId() != null)
                unmatchedEvents.remove(cloudEvent.getId());
            return CompletableFuture.completedFuture(null);
        }

        public CompletableFuture<Void> onInventoryUpdatedAsync(CloudEvent cloudEvent, contoso.erp.consumer.InventoryData data) {
            if (cloudEvent.getId() != null)
                unmatchedEvents.remove(cloudEvent.getId());
            return CompletableFuture.completedFuture(null);
        }

        public CompletableFuture<Void> onProductAddedAsync(CloudEvent cloudEvent, contoso.erp.consumer.ProductData data) {
            if (cloudEvent.getId() != null)
                unmatchedEvents.remove(cloudEvent.getId());
            return CompletableFuture.completedFuture(null);
        }

        public CompletableFuture<Void> onProductDeletedAsync(CloudEvent cloudEvent, contoso.erp.consumer.ProductDeletionData data) {
            if (cloudEvent.getId() != null)
                unmatchedEvents.remove(cloudEvent.getId());
            return CompletableFuture.completedFuture(null);
        }

        public CompletableFuture<Void> onProductUpdatedAsync(CloudEvent cloudEvent, contoso.erp.consumer.ProductUpdatedData data) {
            if (cloudEvent.getId() != null)
                unmatchedEvents.remove(cloudEvent.getId());
            return CompletableFuture.completedFuture(null);
        }

        public CompletableFuture<Void> onEmployeeAddedAsync(CloudEvent cloudEvent, contoso.erp.consumer.EmployeeData data) {
            if (cloudEvent.getId() != null)
                unmatchedEvents.remove(cloudEvent.getId());
            return CompletableFuture.completedFuture(null);
        }

        public CompletableFuture<Void> onEmployeeDeletedAsync(CloudEvent cloudEvent, contoso.erp.consumer.EmployeeDeletionData data) {
            if (cloudEvent.getId() != null)
                unmatchedEvents.remove(cloudEvent.getId());
            return CompletableFuture.completedFuture(null);
        }

        public CompletableFuture<Void> onEmployeeUpdatedAsync(CloudEvent cloudEvent, contoso.erp.consumer.EmployeeUpdatedData data) {
            if (cloudEvent.getId() != null)
                unmatchedEvents.remove(cloudEvent.getId());
            return CompletableFuture.completedFuture(null);
        }

        public CompletableFuture<Void> onPurchaseOrderCreatedAsync(CloudEvent cloudEvent, contoso.erp.consumer.PurchaseOrderData data) {
            if (cloudEvent.getId() != null)
                unmatchedEvents.remove(cloudEvent.getId());
            return CompletableFuture.completedFuture(null);
        }

        public CompletableFuture<Void> onPurchaseOrderUpdatedAsync(CloudEvent cloudEvent, contoso.erp.consumer.PurchaseOrderUpdatedData data) {
                    if (cloudEvent.getId() != null)
                    unmatchedEvents.remove(cloudEvent.getId());
            return CompletableFuture.completedFuture(null);
        }

        public CompletableFuture<Void> onPurchaseOrderDeletedAsync(CloudEvent cloudEvent, Object data) {
            if (cloudEvent.getId() != null)
                unmatchedEvents.remove(cloudEvent.getId());
            return CompletableFuture.completedFuture(null);
        }
    }
    

}
