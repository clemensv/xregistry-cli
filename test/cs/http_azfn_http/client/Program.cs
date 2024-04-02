// Instantiates the Consumer anmd Producer classes and calls their methods
// to send and receive messages.

using CloudNative.CloudEvents;
using CloudNative.CloudEvents.SystemTextJson;
using Contoso.ERP.Producer;
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;

public class Program
{
    public static async Task<int> Main(string[] args)
    {
        string fileName = System.Environment.GetEnvironmentVariable("SENT_FILE")?? "sent.txt";
        var sent = new StreamWriter(fileName, new FileStreamOptions() { Mode = FileMode.Create, Access = FileAccess.Write });
        sent.AutoFlush = true;
        
        JsonEventFormatter formatter = new JsonEventFormatter();
        var loggerFactory = LoggerFactory.Create(builder => builder.AddConsole());
        var logger = loggerFactory.CreateLogger("TestLogger");
        // Create a new instance of the Consumer class.
        
        var producer = EventsEventProducer.CreateForHttpProducer(logger, null, ContentMode.Structured, formatter);
        producer.BeforeSend += (o, e) =>
        {
            sent.WriteLine($"{e.Id}");
            
        };
        
        await producer.SendEmployeeAddedAsync(new Contoso.ERP.Producer.EmployeeData()
        {
            EmployeeId = "123",
            Email = "johndoe@example.com",
            Department = "Sales",
            Name = "John Doe",
            Position = "Sales Manager"
        });
        await producer.SendEmployeeDeletedAsync(new Contoso.ERP.Producer.EmployeeDeletionData()
        {
            EmployeeId = "123",
            Reason = "Termination"
        });
        await producer.SendEmployeeUpdatedAsync(new Contoso.ERP.Producer.EmployeeUpdatedData()
        {
            EmployeeId = "123",
            Email = "johndoe@example.com",
            Department = "Sales",
            Name = "John Doe",
            Position = "Sales Manager"
        });
        await producer.SendInventoryUpdatedAsync(new Contoso.ERP.Producer.InventoryData()
        {
            Location = "Musterstadt",
            ProductId = "abcdef",
            Quantity = 100
        });
        await producer.SendReservationCancelledAsync(new Contoso.ERP.Producer.CancellationData()
        {
            OrderId = "2001272727",
            Reason = "Unknown",
            Status = "Cancelled"
        });
        await producer.SendReservationPlacedAsync(new Contoso.ERP.Producer.OrderData()
        {
            CustomerId = "123",
            OrderId = "abc",
            Total = 1000,
            Items = new List<Contoso.ERP.Producer.OrderData.ItemsItem>()
            {
                new Contoso.ERP.Producer.OrderData.ItemsItem() {
                    ProductId = "123",
                    Price = 10,
                    Quantity = 5
                }
            }
        });
        await producer.SendReservationRefundedAsync(new Contoso.ERP.Producer.RefundData()
        {
            OrderId = "123",
            Amount = 1000,
            Reason = "Unknown",
            Status = "Refunded"
        });
        await producer.SendProductAddedAsync(new Contoso.ERP.Producer.ProductData()
        {
            ProductId = "124",
            Description = "Foo",
            Name = "Foo",
            Price = 123
        });
        await producer.SendProductDeletedAsync(new Contoso.ERP.Producer.ProductDeletionData()
        {
            ProductId = "124",
            Reason = "Discontinued"
        });
        await producer.SendProductUpdatedAsync(new Contoso.ERP.Producer.ProductUpdatedData()
        {
            ProductId = "124",
            Description = "Foo",
            Name = "Foo",
            Price = 123
        });
        await producer.SendPaymentsReceivedAsync(new Contoso.ERP.Producer.PaymentData()
        {
            OrderId = "123",
            Paymentmethod = "Visa",
            Status = "Settled",
            Amount = 1000,
            TransactionId = "abc"
        });
        
        return 0;
    }
}
